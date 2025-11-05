import torch
import torch.nn as nn
import math
import os
from torch.autograd import Variable, Function
from torch import Tensor
from torch.optim import Optimizer
from typing import List, Optional
import sys

torch.ops.load_library(os.path.dirname(os.path.abspath(__file__))+"/libgeondpt.so")

#-------------------------- GEONDSGD --------------------------

class GeoNDSGD(torch.optim.Optimizer):
    r"""
  Applies a 2D convolution over an input signal composed of several input planes using the paraboloid neuron computation.
  
  The arguments ``kernel_size``, ``stride``, ``padding``, ``dilation`` can either be:

        - a single ``int`` -- in which case the same value is used for the height and width dimension.
        - a ``tuple`` of two ints -- in which case, the first `int` is used for the height dimension,
          and the second `int` for the width dimension.
  
  This module currently does not support grouping.
  
  Args:
    params
      Iterable of parameters to optimize or dicts defining parameter groups.
    lr
      Learning rate (default: 1e-3).
    momentum
      Momentum factor (default: 0)
    weight_decay
      Weight decay (default: 0)
    dampening
      Dampening for momentum (default: 0)
    nesterov
      Enables Nesterov momentum (default: False)
      
----
      
  **Example:**

    >>> pb = gd.Paraboloid(20, 30)
    >>> input = torch.randn(128, 20)
    >>> output = pb(input)
    >>> print(output.size())
    torch.Size([128, 30])

    """
    def __init__(self, params, lr=0.001, momentum=0, dampening=0,
                 weight_decay=0, nesterov=False, *, maximize=False, foreach: Optional[bool] = None):
        if lr < 0.0:
            raise ValueError("Invalid learning rate: {}".format(lr))
        if momentum < 0.0:
            raise ValueError("Invalid momentum value: {}".format(momentum))
        if weight_decay < 0.0:
            raise ValueError("Invalid weight_decay value: {}".format(weight_decay))

        defaults = dict(lr=lr, momentum=momentum, dampening=dampening,
                        weight_decay=weight_decay, nesterov=nesterov,
                        maximize=maximize, foreach=foreach)
        if nesterov and (momentum <= 0 or dampening != 0):
            raise ValueError("Nesterov momentum requires a momentum and zero dampening")
        super(GeoNDSGD, self).__init__(params, defaults)

    def __setstate__(self, state):
        super().__setstate__(state)
        for group in self.param_groups:
            group.setdefault('nesterov', False)
            group.setdefault('maximize', False)
            group.setdefault('foreach', None)

    @torch.no_grad()
    def step(self, closure=None):
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for group in self.param_groups:
            params_with_grad = []
            d_p_list = []
            momentum_buffer_list = []
            has_sparse_grad = False

            for p in group['params']:
                if p.grad is not None:
                    params_with_grad.append(p)
                    d_p_list.append(p.grad)
                    if p.grad.is_sparse:
                        has_sparse_grad = True

                    state = self.state[p]
                    if 'momentum_buffer' not in state:
                        momentum_buffer_list.append(None)
                    else:
                        momentum_buffer_list.append(state['momentum_buffer'])

            geondsgd(params_with_grad,
                d_p_list,
                momentum_buffer_list,
                weight_decay=group['weight_decay'],
                momentum=group['momentum'],
                lr=group['lr'],
                dampening=group['dampening'],
                nesterov=group['nesterov'],
                maximize=group['maximize'],
                has_sparse_grad=has_sparse_grad,
                foreach=group['foreach'])

            # update momentum_buffers in state
            for p, momentum_buffer in zip(params_with_grad, momentum_buffer_list):
                state = self.state[p]
                state['momentum_buffer'] = momentum_buffer

        return loss


def geondsgd(params: List[Tensor],
        d_p_list: List[Tensor],
        momentum_buffer_list: List[Optional[Tensor]],
        has_sparse_grad: bool = None,
        foreach: bool = None,
        *,
        weight_decay: float,
        momentum: float,
        lr: float,
        dampening: float,
        nesterov: bool,
        maximize: bool):
    
    foreach = False

    if foreach is None:
        foreach = False

    if foreach and torch.jit.is_scripting():
        raise RuntimeError('torch.jit.script not supported with foreach optimizers')

    if foreach and not torch.jit.is_scripting():
        func = _multi_tensor_geondsgd
    else:
        func = _single_tensor_geondsgd

    func(params,
         d_p_list,
         momentum_buffer_list,
         weight_decay=weight_decay,
         momentum=momentum,
         lr=lr,
         dampening=dampening,
         nesterov=nesterov,
         has_sparse_grad=has_sparse_grad,
         maximize=maximize)

def _single_tensor_geondsgd(params: List[Tensor],
                       d_p_list: List[Tensor],
                       momentum_buffer_list: List[Optional[Tensor]],
                       *,
                       weight_decay: float,
                       momentum: float,
                       lr: float,
                       dampening: float,
                       nesterov: bool,
                       maximize: bool,
                       has_sparse_grad: bool):

    for i, param in enumerate(params):

        d_p = d_p_list[i]
        if hasattr(param, "isParaboloid"):        
            if momentum != 0:
                buf = momentum_buffer_list[i]

                if buf is None:
                    buf = torch.clone(d_p).detach()
                    momentum_buffer_list[i] = buf
                else:
                    buf.mul_(momentum).add_(d_p, alpha=1 - dampening)

            else:
                buf = torch.clone(d_p).detach()
            pu = torch.ops.ptgeondsgdfree.getparupdate(d_p, buf, param, float(param.d), param.lr_factor*lr, momentum, dampening, nesterov, param.wd_factor*weight_decay)
            
            alpha = 1 if maximize else -1

            param.add_(pu[0], alpha=alpha)
            
            if momentum != 0:
              if (param.lr_factor*lr > 0):
                momentum_buffer_list[i] = pu[0]/(param.lr_factor*lr);
              else:
                momentum_buffer_list[i] = pu[0];
        else:
            if weight_decay != 0:
                d_p = d_p.add(param, alpha=weight_decay)

            if momentum != 0:
                buf = momentum_buffer_list[i]

                if buf is None:
                    buf = torch.clone(d_p).detach()
                    momentum_buffer_list[i] = buf
                else:
                    buf.mul_(momentum).add_(d_p, alpha=1 - dampening)

                if nesterov:
                    d_p = d_p.add(buf, alpha=momentum)
                else:
                    d_p = buf

            alpha = lr if maximize else -lr
            param.add_(d_p, alpha=alpha)


def _multi_tensor_geondsgd(params: List[Tensor],
                      grads: List[Tensor],
                      momentum_buffer_list: List[Optional[Tensor]],
                      *,
                      weight_decay: float,
                      momentum: float,
                      lr: float,
                      dampening: float,
                      nesterov: bool,
                      maximize: bool,
                      has_sparse_grad: bool):
    if len(params) == 0:
        return

    if has_sparse_grad is None:
        has_sparse_grad = any([grad.is_sparse for grad in grads])

    if weight_decay != 0:
        grads = torch._foreach_add(grads, params, alpha=weight_decay)

    if momentum != 0:
        bufs = []

        all_states_with_momentum_buffer = True
        for i in range(len(momentum_buffer_list)):
            if momentum_buffer_list[i] is None:
                all_states_with_momentum_buffer = False
                break
            else:
                bufs.append(momentum_buffer_list[i])

        if all_states_with_momentum_buffer:
            torch._foreach_mul_(bufs, momentum)
            torch._foreach_add_(bufs, grads, alpha=1 - dampening)
        else:
            bufs = []
            for i in range(len(momentum_buffer_list)):
                if momentum_buffer_list[i] is None:
                    buf = momentum_buffer_list[i] = torch.clone(grads[i]).detach()
                else:
                    buf = momentum_buffer_list[i]
                    buf.mul_(momentum).add_(grads[i], alpha=1 - dampening)

                bufs.append(buf)

        if nesterov:
            torch._foreach_add_(grads, bufs, alpha=momentum)
        else:
            grads = bufs

    alpha = lr if maximize else -lr
    if not has_sparse_grad:
        torch._foreach_add_(params, grads, alpha=alpha)
    else:
        for i in range(len(params)):
            params[i].add_(grads[i], alpha=alpha)
