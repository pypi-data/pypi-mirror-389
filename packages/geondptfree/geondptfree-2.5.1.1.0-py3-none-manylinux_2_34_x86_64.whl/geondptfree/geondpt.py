import torch
import torch.nn as nn
from torch.nn import functional as F
import math
import numpy
import os
from torch.autograd import Variable, Function
from torch import Tensor
from torch.optim import Optimizer
from typing import List, Optional
import time

torch.ops.load_library(os.path.dirname(os.path.abspath(__file__))+"/libgeondpt.so")

def prescale_input(x):
  xmax = torch.max(x)
  xmin = torch.min(x)
  return( (2*(x-xmin)*(1/(xmax-xmin))) - torch.ones(x.shape).to(x.device) )
  


def spotlightinit(m, d, input_factor, h_factor = 1.0, p_factor = -0.000001):
  h = torch.zeros(m,d)
  h0 = h_factor*torch.ones(m)
  p = torch.empty(m,d)
  p.data.uniform_(-input_factor, input_factor)
  p0 = p_factor*torch.ones(m)
  return(h, p, h0, p0)



def pnnconvert(w, b, offset=20.0):
  H, D = w.size()
  tmpd=torch.sqrt(torch.sum(torch.square(w), dim=1))
  h = Variable(torch.div(w, tmpd.repeat(D,1).t()), requires_grad = False)
  tmpb = torch.div(b,tmpd)
  factor = 1.
  h0 = Variable(factor*(tmpb + offset), requires_grad = False)
  p = Variable(h.mul((factor*offset) - tmpb.repeat(D,1).t()), requires_grad = False)
  h = factor*h
  return(h, p, h0)



def liveinit(pars, m, k, x, p_factor):
  n = x.size(dim = 0)
  start = m - k
  finish = start + n
  d = int(torch.numel(x)/n)
  if (finish>=m):
    finish = m
  for i in range(start, finish):
    for j in range(0,d):
      pars.data[ m*(d+1) + (i*d) + j ] = x.data[(i-start)][j]
    pars.data[m*((2*d)+1)+i] = p_factor
  return(finish-start)



#-------------------------- PARABOLOID --------------------------


class ParaboloidFunction(Function):
  @staticmethod
  def forward(ctx, input, pars, output_factor, grad_factor):
    output, hsum = torch.ops.ptparaboloidfree.forward(input, pars, output_factor)
    ctx.save_for_backward(input, pars, hsum)
    ctx.output_factor = output_factor
    ctx.grad_factor = grad_factor
    return output
  @staticmethod
  def backward(ctx, grad_output):
    input, pars, hsum = ctx.saved_tensors
    grad_input, grad_pars = torch.ops.ptparaboloidfree.backward(grad_output, input, pars, hsum, ctx.output_factor)
    return ctx.grad_factor*grad_input, grad_pars, None, None



class Paraboloid(nn.Module):
  r"""
  Passes the incoming data through a layer of paraboloid neurons.
  
  Args:
  
    in_features
      Size of each input sample.
      
    out_features
      Size of each output sample.
      
    output_factor
      Multiplies the output of the module. Default: ``0.1``.
      
    input_factor
      Multiplies the input before passing it through the layer. Default: ``0.01``.
      
    lr_factor
      Multiplies the learning rate applied to the parameters by the optimizer. Default: ``100``.
      
    init
      Selects the initialization method for the parameters. Valid options are ``'spotlight'``, ``'live'``, ``'linear'``. Default: ``'live'``.
      
    h_factor
      Affects the ``'spotlight'`` and ``'live'`` initializations. Multiplies the magnitude of the directrix vector. Default: ``1.0``.
      
    p_factor
      Affects the ``'spotlight'`` and ``'live'`` initializations. Determines the offset of the focus from the data subspace. Default: ``-0.000001``.
      
    initw
      Used with the ``'linear'`` initialization. Assigns specific values to the weights of the linear neurons pre-conversion to paraboloid. Default: ``None``.
      
    initb
      Used with the ``'linear'`` initialization. Assigns specific values to the bias of the linear neurons pre-conversion to paraboloid. Default: ``None``.

----
      
  **Shape:**
  
    - Input: :math:`(*, H_{in})` where :math:`*` means any number of
      dimensions including none and :math:`H_{in} = \text{in_features}`.
      
    - Output: :math:`(*, H_{out})` where all but the last dimension
      are the same shape as the input and :math:`H_{out} = \text{out_features}`.

----

  **Example:**

    >>> import torch
    >>> import geondpt as gd
    >>> pb = gd.Paraboloid(20, 30)
    >>> input = torch.randn(128, 20)
    >>> output = pb(input)
    >>> print(output.size())
    torch.Size([128, 30])

  """
  def __init__(self, input_features, output_features, bias = True, device = None, dtype = None, output_factor = .01, input_factor = 0.01, lr_factor = 10., wd_factor=1., init = 'live', h_factor = 1.0, p_factor = -0.000001, grad_factor = 1., init_from_numpy = None):
    super(Paraboloid, self).__init__()
    tmp = torch.empty(output_features, input_features+1)
    stdv = 1. / math.sqrt(tmp.size(1))
    tmp.data.uniform_(-stdv, stdv)
    
    self.live = 0
    if init == "spotlight":
      tmph, tmpp, tmph0, tmpp0 = spotlightinit(output_features, input_features, input_factor, h_factor, p_factor)
    elif init == "live":
      tmph, tmpp, tmph0, tmpp0 = spotlightinit(output_features, input_features, input_factor, h_factor, p_factor)
      #tmpp = 10.*torch.ones_like(tmpp)
      self.live = output_features
    elif init == "linear":
      w = tmp[:, 0:input_features]/input_factor
      b = tmp[:, input_features]/input_factor
      tmph, tmpp, tmph0 = pnnconvert(w, b, 20.0)
      tmpp0 = 0.01*torch.ones(output_features)
    else:
      raise Exception("Unknown Paraboloid initialization.")      
    self.h_factor = h_factor
    self.p_factor = p_factor
    self.input_features = input_features
    self.output_features = output_features
    if (dtype != None):
      tmph0 = tmph0.to(dtype)
      tmph = tmph0.to(dtype)
      tmpp0 = tmph0.to(dtype)
      tmpp = tmph0.to(dtype)
    if (device != None):
      tmph0 = tmph0.to(device)
      tmph = tmph0.to(device)
      tmpp0 = tmph0.to(device)
      tmpp = tmph0.to(device)
    if (init_from_numpy is not None):
      self.live = 0;
      self.pars = nn.Parameter(torch.from_numpy(init_from_numpy))
    else:
      self.pars = nn.Parameter(torch.concat( (tmph0,torch.reshape(tmph,(-1,)),torch.reshape(tmpp,(-1,)),tmpp0), dim=0))
    self.output_factor = output_factor
    self.pars.d = input_features
    self.pars.isParaboloid = True
    self.pars.lr_factor = lr_factor
    self.pars.wd_factor = wd_factor
    self.input_factor = input_factor
    self.grad_factor = grad_factor

  def forward(self, input):
    x = self.input_factor*input
    if (self.live>0):
      n = x.size(dim=0)
      self.live = self.live - liveinit(self.pars, self.output_features, self.live, x, self.p_factor)
    return ParaboloidFunction.apply(x, self.pars, self.output_factor, self.grad_factor)



#-------------------------- PARACONV2D --------------------------


class ParaConv2dFunction(Function):
  @staticmethod
  def forward(ctx, input, pars, output_factor, kernel_size, stride, dilation, skip_input_grad, grad_factor):
  
    output, hsum = torch.ops.ptparaconv2dfree.forward(input, pars, float(output_factor), kernel_size, stride, dilation)
    ctx.save_for_backward(input, pars, hsum)
    ctx.output_factor = output_factor
    ctx.kernel_size = kernel_size
    ctx.stride = stride
    ctx.dilation = dilation
    ctx.skip_input_grad = skip_input_grad
    ctx.grad_factor = grad_factor
    return output
  @staticmethod
  def backward(ctx, grad_output):
    input, pars, hsum = ctx.saved_tensors
    grad_input, grad_pars = torch.ops.ptparaconv2dfree.backward(grad_output, input, pars, hsum, float(ctx.output_factor), ctx.kernel_size, ctx.stride, ctx.dilation, ctx.skip_input_grad)
    return ctx.grad_factor*grad_input, grad_pars, None, None, None, None, None, None



class ParaConv2d(nn.Module):
  r"""
  Applies a 2D convolution over an input signal composed of several input planes using the paraboloid neuron computation.
  
  The arguments ``kernel_size``, ``stride``, ``padding``, ``dilation`` can either be:

        - a single ``int`` -- in which case the same value is used for the height and width dimension.
        - a ``tuple`` of two ints -- in which case, the first `int` is used for the height dimension,
          and the second `int` for the width dimension.
  
  This module currently does not support grouping.
  
  Args:
    in_channels
      Number of channels in the input image.
      
    out_channels
      Number of channels produced by the convolution.
      
    kernel_size
      Size of the convolving kernel.
      
    stride
      Stride of the convolution. Default: ``1``.
      
    padding
      Padding added to all four sides of the input. Default: ``0``.
    
    dilation
      Spacing between kernel elements. Default: ``1``.
    
    output_factor
      Multiplies the output of the module. Default: ``0.01``.

    input_factor
      Multiplies the input before passing it through the layer. Default: ``0.01``.
    
    lr_factor
      Multiplies the learning rate applied to the parameters by the optimizer. Default: ``100``.
      
    skip_input_grad
      If set to ``True``, it skips the computation of the delta signal, should only be set for the very first layer of the network. Default: ``False``.
    
    init
      Selects the initialization method for the parameters. Valid options are ``'spotlight'``, ``'linear'``. Default: ``'spotlight'``.
      
    initw
      Used with the ``'linear'`` initialization. Assigns specific values to the weights of the linear neurons pre-conversion to paraboloid. Default: ``None``.
      
    initb
      Used with the ``'linear'`` initialization. Assigns specific values to the bias of the linear neurons pre-conversion to paraboloid. Default: ``None``.

----
      
  **Shape:**
  
    - Input: :math:`(N, C_{in}, H_{in}, W_{in})`
    
    - Output: :math:`(N, C_{out}, H_{out}, W_{out})`, where

          .. math::
              H_{out} = \left\lfloor\frac{H_{in}  + 2 \times \text{padding}[0] - \text{dilation}[0]
                        \times (\text{kernel_size}[0] - 1) - 1}{\text{stride}[0]} + 1\right\rfloor

          .. math::
              W_{out} = \left\lfloor\frac{W_{in}  + 2 \times \text{padding}[1] - \text{dilation}[1]
                        \times (\text{kernel_size}[1] - 1) - 1}{\text{stride}[1]} + 1\right\rfloor

----

  **Example:**

    >>> pb = gd.ParaConv2d(16, 33, (3, 5), stride=(2, 1), padding=(4, 2), dilation=(3, 1))
    >>> input = torch.randn(20, 16, 50, 100)
    >>> output = pb(input)


  """
  def __init__(self, in_channels, out_channels, kernel_size, stride=1, padding=0, dilation=1, bias=True, padding_mode='constant', device = None, dtype = None, output_factor = 0.01, input_factor = 0.01, lr_factor = 100, wd_factor=10., skip_input_grad = False, init = 'spotlight', h_factor = 1.0, p_factor = -0.000001, grad_factor = 1., init_from_numpy = None):
    super(ParaConv2d, self).__init__()

    if (type(kernel_size) == int):
      kernel_size = [kernel_size, kernel_size]
    if (type(dilation) == int):
      dilation = [dilation, dilation]
    if (type(stride) == int):
      stride = [stride, stride]
    if (type(padding) == int):
      padding = (padding, padding, padding, padding)
      #padding = [padding, padding]
    input_features = in_channels*kernel_size[0]*kernel_size[1]
    tmp = torch.empty(out_channels, input_features+1)
    stdv = 1. / math.sqrt(tmp.size(1))
    tmp.data.uniform_(-stdv, stdv)
    if init == 'spotlight':
      tmph, tmpp, tmph0, tmpp0 = spotlightinit(out_channels, input_features, input_factor, h_factor, p_factor)
    elif init == "linear":
      w = tmp[:, 0:input_features]
      b = tmp[:, input_features]
      tmph, tmpp, tmph0 = pnnconvert(w, b, 20.0)
      tmpp0 = 0.01*torch.ones(output_features)
    else:
      raise Exception("Unknown Paraboloid initialization.")      
    self.in_channels = in_channels
    self.out_channels = out_channels
    if (dtype != None):
      tmph0 = tmph0.to(dtype)
      tmph = tmph0.to(dtype)
      tmpp0 = tmph0.to(dtype)
      tmpp = tmph0.to(dtype)
    if (device != None):
      tmph0 = tmph0.to(device)
      tmph = tmph0.to(device)
      tmpp0 = tmph0.to(device)
      tmpp = tmph0.to(device)
    if (init_from_numpy is not None):
      self.pars = nn.Parameter(torch.from_numpy(init_from_numpy))
    else:
      self.pars = nn.Parameter(torch.concat( (tmph0,torch.reshape(tmph,(-1,)),torch.reshape(tmpp,(-1,)),tmpp0), dim=0))
    self.pars.d = int(in_channels*torch.prod(torch.Tensor(kernel_size)))
    self.pars.isParaboloid = True
    self.pars.lr_factor = lr_factor
    self.pars.wd_factor = wd_factor
    self.output_factor = output_factor

    self.in_channels = in_channels
    self.out_channels = out_channels
    self.kernel_size = torch.tensor(kernel_size, dtype = torch.int)
    self.stride = torch.tensor(stride, dtype = torch.int)
    self.dilation = torch.tensor(dilation, dtype = torch.int)
    self.skip_input_grad = skip_input_grad
    self.padding = padding
    self.padding_mode = padding_mode
    self.input_factor = input_factor
    self.grad_factor = grad_factor
    self.forward(torch.zeros(1, in_channels, kernel_size[0], kernel_size[1])) # DO NOT REMOVE THIS LINE

  def forward(self, input):
    x = self.input_factor*input
    x = F.pad(x, self.padding, mode = self.padding_mode)
    return ParaConv2dFunction.apply(x, self.pars, self.output_factor, self.kernel_size, self.stride, self.dilation, self.skip_input_grad, self.grad_factor)



#-------------------------- PARACONV1D --------------------------


class ParaConv1d(nn.Module):
  def __init__(self, in_channels, out_channels, kernel_size, stride=1, padding=0, dilation=1, bias=True, padding_mode='constant', device = None, dtype = None, output_factor = 0.01, input_factor = 0.01, lr_factor = 100, wd_factor=10., skip_input_grad = False, init = 'spotlight', h_factor = 1.0, p_factor = -0.000001, grad_factor = 1., init_from_numpy = None):
    super(ParaConv1d, self).__init__()
    
    print("*WARNING* GeoND ParaConv1d is a late addition, has not been thoroughly tested and uses the ParaConv2d functions, it may not perform well.")

    if (type(kernel_size) == int):
      kernel_size = [kernel_size, 1]
    if (type(dilation) == int):
      dilation = [dilation, 1]
    if (type(stride) == int):
      stride = [stride, 1]
    if (type(padding) == int):
      padding = (padding, padding, 0, 0)
    input_features = in_channels*kernel_size[0]
    tmp = torch.empty(out_channels, input_features+1)
    stdv = 1. / math.sqrt(tmp.size(1))
    tmp.data.uniform_(-stdv, stdv)
    if init == 'spotlight':
      tmph, tmpp, tmph0, tmpp0 = spotlightinit(out_channels, input_features, input_factor, h_factor, p_factor)
    elif init == "linear":
      w = tmp[:, 0:input_features]
      b = tmp[:, input_features]
      tmph, tmpp, tmph0 = pnnconvert(w, b, 20.0)
      tmpp0 = 0.01*torch.ones(output_features)
    else:
      raise Exception("Unknown Paraboloid initialization.")      
    self.in_channels = in_channels
    self.out_channels = out_channels
    if (dtype != None):
      tmph0 = tmph0.to(dtype)
      tmph = tmph0.to(dtype)
      tmpp0 = tmph0.to(dtype)
      tmpp = tmph0.to(dtype)
    if (device != None):
      tmph0 = tmph0.to(device)
      tmph = tmph0.to(device)
      tmpp0 = tmph0.to(device)
      tmpp = tmph0.to(device)
    if (init_from_numpy is not None):
      self.pars = nn.Parameter(torch.from_numpy(init_from_numpy))
    else:
      self.pars = nn.Parameter(torch.concat( (tmph0,torch.reshape(tmph,(-1,)),torch.reshape(tmpp,(-1,)),tmpp0), dim=0))
    self.pars.d = int(in_channels*torch.prod(torch.Tensor(kernel_size)))
    self.pars.isParaboloid = True
    self.pars.lr_factor = lr_factor
    self.pars.wd_factor = wd_factor
    self.output_factor = output_factor

    self.in_channels = in_channels
    self.out_channels = out_channels
    self.kernel_size = torch.tensor(kernel_size, dtype = torch.int)
    self.stride = torch.tensor(stride, dtype = torch.int)
    self.dilation = torch.tensor(dilation, dtype = torch.int)
    self.skip_input_grad = skip_input_grad
    self.padding = padding
    self.padding_mode = padding_mode
    self.input_factor = input_factor
    self.grad_factor = grad_factor
    self.forward(torch.zeros(1, in_channels, kernel_size[0], kernel_size[1])) # DO NOT REMOVE THIS LINE

  def forward(self, input):
    x = self.input_factor*input
    x = torch.unsqueeze(x,3)
    x = F.pad(x, self.padding, mode = self.padding_mode)
    output = ParaConv2dFunction.apply(x, self.pars, self.output_factor, self.kernel_size, self.stride, self.dilation, self.skip_input_grad, self.grad_factor)
    return torch.squeeze(output,3)



#---------------------- PARABOLOIDRESIDUAL ----------------------


class ParaboloidResidualFunction(Function):
  @staticmethod
  def forward(ctx, input, pars, output_factor, sum_factor, grad_factor):
    output, hsum = torch.ops.ptparaboloidfree.forward(input, pars, output_factor)
    ctx.save_for_backward(input, pars, hsum)
    ctx.output_factor = output_factor
    ctx.sum_factor = sum_factor
    ctx.grad_factor = grad_factor
    return input + (sum_factor*output)
  @staticmethod
  def backward(ctx, grad_output):
    input, pars, hsum = ctx.saved_tensors
    grad_input, grad_pars = torch.ops.ptparaboloidfree.backward(grad_output, input, pars, hsum, ctx.output_factor)
    return (grad_output + (ctx.sum_factor*ctx.grad_factor*grad_input)), grad_pars, None, None, None



class ParaboloidResidual(nn.Module):
  r"""
  Passes the incoming data through a layer of paraboloid neurons.
  
  Args:
  
    in_features
      Size of each input sample.
      
    out_features
      Size of each output sample.
      
    output_factor
      Multiplies the output of the module. Default: ``0.1``.
      
    input_factor
      Multiplies the input before passing it through the layer. Default: ``0.01``.
      
    lr_factor
      Multiplies the learning rate applied to the parameters by the optimizer. Default: ``100``.
      
    init
      Selects the initialization method for the parameters. Valid options are ``'spotlight'``, ``'live'``, ``'linear'``. Default: ``'live'``.
      
    h_factor
      Affects the ``'spotlight'`` and ``'live'`` initializations. Multiplies the magnitude of the directrix vector. Default: ``1.0``.
      
    p_factor
      Affects the ``'spotlight'`` and ``'live'`` initializations. Determines the offset of the focus from the data subspace. Default: ``-0.000001``.
      
    initw
      Used with the ``'linear'`` initialization. Assigns specific values to the weights of the linear neurons pre-conversion to paraboloid. Default: ``None``.
      
    initb
      Used with the ``'linear'`` initialization. Assigns specific values to the bias of the linear neurons pre-conversion to paraboloid. Default: ``None``.

----
      
  **Shape:**
  
    - Input: :math:`(*, H_{in})` where :math:`*` means any number of
      dimensions including none and :math:`H_{in} = \text{in_features}`.
      
    - Output: :math:`(*, H_{out})` where all but the last dimension
      are the same shape as the input and :math:`H_{out} = \text{out_features}`.

----

  **Example:**

    >>> import torch
    >>> import geondpt as gd
    >>> pb = gd.Paraboloid(20, 30)
    >>> input = torch.randn(128, 20)
    >>> output = pb(input)
    >>> print(output.size())
    torch.Size([128, 30])

  """
  def __init__(self, input_features, sum_factor=0.00001, bias = True, device = None, dtype = None, output_factor = .01, input_factor = 0.01, lr_factor = 10., wd_factor=1., init = 'spotlight', h_factor = 1.0, p_factor = -0.000001, grad_factor = 1., init_from_numpy = None):
    super(ParaboloidResidual, self).__init__()
    output_features = input_features
    tmp = torch.empty(output_features, input_features+1)
    stdv = 1. / math.sqrt(tmp.size(1))
    tmp.data.uniform_(-stdv, stdv)
    self.live = 0
    if init == "spotlight":
      tmph, tmpp, tmph0, tmpp0 = spotlightinit(output_features, input_features, input_factor, h_factor, p_factor)
    elif init == "live":
      tmph, tmpp, tmph0, tmpp0 = spotlightinit(output_features, input_features, input_factor, h_factor, p_factor)
      #tmpp = 10.*torch.ones_like(tmpp)
      self.live = output_features
    elif init == "linear":
      w = tmp[:, 0:input_features]/input_factor
      b = tmp[:, input_features]/input_factor
      tmph, tmpp, tmph0 = pnnconvert(w, b, 20.0)
      tmpp0 = 0.01*torch.ones(output_features)
    else:
      raise Exception("Unknown Paraboloid initialization.")      
    self.h_factor = h_factor
    self.p_factor = p_factor
    self.input_features = input_features
    self.output_features = output_features
    if (dtype != None):
      tmph0 = tmph0.to(dtype)
      tmph = tmph0.to(dtype)
      tmpp0 = tmph0.to(dtype)
      tmpp = tmph0.to(dtype)
    if (device != None):
      tmph0 = tmph0.to(device)
      tmph = tmph0.to(device)
      tmpp0 = tmph0.to(device)
      tmpp = tmph0.to(device)
    if (init_from_numpy is not None):
      self.live = 0;
      self.pars = nn.Parameter(torch.from_numpy(init_from_numpy))
    else:
      self.pars = nn.Parameter(torch.concat( (tmph0,torch.reshape(tmph,(-1,)),torch.reshape(tmpp,(-1,)),tmpp0), dim=0))
    self.output_factor = output_factor
    self.sum_factor = sum_factor
    self.pars.d = input_features
    self.pars.isParaboloid = True
    self.pars.lr_factor = lr_factor
    self.pars.wd_factor = wd_factor
    self.input_factor = input_factor
    self.grad_factor = grad_factor

  def forward(self, input):
    x = self.input_factor*input
    if (self.live>0):
      n = x.size(dim=0)
      self.live = self.live - liveinit(self.pars, self.output_features, self.live, x, self.p_factor)
    return ParaboloidResidualFunction.apply(x, self.pars, self.output_factor, self.sum_factor, self.grad_factor)

