from .structs import LoadedSParamFile
from .bodefano import BodeFano
from .stabcircle import StabilityCircle
from .networks import Networks
from .sparams import SParam, SParams

import skrf, math, os
import numpy as np
import fnmatch


class ExpressionParser:

    @staticmethod
    def eval(code: str, \
        available_networks: "list[LoadedSParamFile]", \
        selected_networks: "list[LoadedSParamFile]", \
        plot_fn: "callable[np.ndarray,np.ndarray,str,str]"):
        
        SParam.plot_fn = plot_fn

        def select_networks(network_list: list[LoadedSParamFile], pattern: str, single: bool) -> Networks:
            nws = []
            for nw in network_list:
                if pattern is None or fnmatch.fnmatch(nw.sparam.network.name, pattern):
                    nws.append(nw.sparam.network)
            if single:
                if len(nws) != 1:
                    raise RuntimeError(f'The pattern "" matched {len(nws)} networks, but need exactly one')
            return Networks(nws)

        def sel_nws(pattern: str = None) -> Networks:
            return select_networks(selected_networks, pattern, single=False)
        
        def nws(pattern: str) -> Networks:
            return select_networks(selected_networks, pattern, single=False)
        
        def nw(pattern: str) -> Networks:
            return select_networks(selected_networks, pattern, single=True)

        vars_global = {}
        vars_local = {
            'Networks': Networks,
            'SParams': SParams,
            'nw': nw,
            'nws': nws,
            'sel_nws': sel_nws,
            'math': math,
            'np': np,
        }
        
        for code_line in code.split('\n'):
            code_linestripped = code_line.strip()
            if code_linestripped.startswith('#'):
                continue
            if len(code_linestripped) < 1:
                continue
            _ = eval(code_linestripped, vars_global, vars_local)


    @staticmethod
    def help() -> str:
            return '''Basics
======

The basic concept is to load one or multiple networks, get a specific S-parameter (s), and plot it (plot):

    nws("Amplifier.s2p").s(2,1).plot("IL")

Which could be re-written as:
    
    n = nws("*.s2p") # type: Networks
    s = n.s(2,1) # type: SParams
    s.plot("IL")

The expression use Python syntax. You also have access to `math` and `np` (numpy).


Objects
=======

Networks
--------

    A container for one or more S-parameter networks.

    Note that any operation on the object might fail silently. For example, if an object contains a 1-port
    and a 2-port, and you attempt to invert the object (an operation that only works on 2-ports), the 1-port
    will silently be dropped.

    Constructor

        Network(<name_or_partial_name>)
            Returns the networks that match the provided name; e.g. Networks("Amplifier") would match
            a file named "Amplifier.s2p" or "MyAmplifier01.s2p".

    Methods

        s(<egress_port>,<ingress_port>) -> SParams
            Gets an S-parameters.

        invert() -> Networks
            Inverts the ports (e.g. for de-embedding).

        flip() -> Networks
            Flips the ports (e.g. to use it in reverse direction).

        half() -> Networks
            Chops the network in half (e.g. for 2xTHRU de-embedding).

        k() -> SParams
            Returns the K (Rollet) stability factor (should be >1, or >0 dB).

        mu(<mu=1>) -> SParams
            Returns the µ or µ' (Edwards-Sinsky) stability factor (should be >1, or >0 dB;
            mu must be 1 or 2, default is 1).

        crop_f([f_start], [f_end]) -> Networks
            Returns the same network, but with a reduced frequency range
        
        add_sr(resistance[, <port=1>]) -> Networks
            Returns a network with a series resistance attached to the specified port.
            Works only for 1-ports and 2-ports.
        
        add_sl(inductance[, <port=1>]) -> Networks
            Returns a network with a series inductance attached to the specified port.
            Works only for 1-ports and 2-ports.
        
        add_sc(capacitance[, <port=1>]) -> Networks
            Returns a network with a series inductance attached to the specified port.
            Works only for 1-ports and 2-ports.
        
        add_pr(resistance[, <port=1>]) -> Networks
            Returns a network with a parallel resistance attached to the specified port.
            Works only for 1-ports and 2-ports.
        
        add_pl(inductance[, <port=1>]) -> Networks
            Returns a network with a parallel inductance attached to the specified port.
            Works only for 1-ports and 2-ports.
        
        add_pc(capacitance[, <port=1>]) -> Networks
            Returns a network with a parallel inductance attached to the specified port.
            Works only for 1-ports and 2-ports.
        
        add_tl(degrees, frequency_hz=1e9[, <z0=default>][, <loss=0>][, <port=1>]) -> Networks
            Returns a network with a transmission line attached to the specified port.
            Works only for 1-ports and 2-ports. The length is specified in degrees at the given frequency.
            The loss is the real part of the propagation constant.
            If Z0 is not provided, the reference impedance of the corresponding port is used.
        
        rl_avg(f_start_hz=-inf, f_stop_hz=+inf) -> SParams
            Calculates the average return loss over the given frequency range.
        
        rl_opt(f_integrate_start_hz=-inf, f_integrate_stop_hz=+inf, f_target_start_hz=-inf, f_target_stop_hz=+inf) -> SParams
            Integrates the return loss over the given integration frequency range, then uses
            the Bode-Fano limit to calculate the maximum achievable return loss over the
            given target frequency range.
        
        plot_stab(frequency_hz, [<port=2>], [<n_points=101>], ([<label=None>],[<style="-">]):
            Plots the stability circle at the given frequency. Set port=1 if you want to calculate the stability at
            the input, otherwise the output is calculated. It adds "s.i." (stable inside circle) or "s.o." (stable outside
            of the circle) to the plot name.

    Unary Operators

        ~
            Same as invert().

    Binary Operators

        **
            Cascades two networks.

SParams
-------

    Methods

        plot([<label=None>],[<style="-">]) -> Network
            Plots the data. <label> is any string.
            <style> is a matplotlib-compatible format (e.g. "-", ":", "--", "o-").

        db() -> Network
            Converts all values to dB.

        abs() -> SParam
            Takes abs() of each value.

        crop_f([f_start=-inf], [f_end=+inf]) -> SParam.
            Returns the same S-Param, but with a reduced frequency range.

    Unary Operators

        ~
            Takes the inverse (i.e. 1/x) of each value.

    Binary Operators

        + - * /
            Applies the corresponding mathematical operator.
            Each operand can also be a numeric constant.


Functions
=========

nws(pattern)
------------

Returns a Networks object that contains all networks that match the given pattern, e.g. '*.s2p'. Note that
this returns an empty Networks object if the pattern does not match anything.


sel_nws(pattern)
----------------

same as nws(), except that it only matches networks that are currently selected.


nw(pattern)
-----------

same as nws(), except that it raises an error if not exactly one network is matched.


Examples
========

Basic
-----

    nws().s(1,1).plot("RL")
    sel_nws().s(1,2).plot("Reverse IL")
    nws("Amplifier.s2p").s(2,1).plot("IL")
    nws("Amplifier.s2p").s(1,1).plot("RL",":")

Objects vs. Functions
---------------------

The following examples are all identical:

    nws("Amplifier.s2p").s(1,1).plot("RL",":")
    Networks("Amplifier.s2p").s(1,1).plot("RL",":")
    plot(s(nws("Amplifier.s2p"),1,1),"RL",":")

Advanced
--------

    # calculate directivity (S42/S32) of a directional coupler
    # note that this example requires plotting in linear units, as the values are already converted to dB
    (nws("Coupler.s2p").s(4,2).db() / nw("Coupler.s2p").s(3,2).db()).plot("Directivity")

    # de-embed a 2xTHRU
    (nws("2xThru").half().invert() ** nw("DUT") ** nw("2xThru").half().invert().flip()).s(2,1).plot("De-embedded")

    # crop frequency range; this can be handy e.g. if you want to see the Smith-chart only for a specific frequency range
    nws("Amplifier.s2p").crop_f(1e9,10e9).s(1,1).plot("RL",":")

    # calculate stability factor
    nws("Amplifier").mu().plot("µ Stability Factor",":")

    # add elements to a network (in this case, a parallel cap, followed by a short transmission line)
    nws("Amplifier").s(1,1).plot("Baseline",":")
    nws("Amplifier").add_pc(400e-15).add_tl(7,2e9,25).s(1,1).plot("Optimized","-")
'''
