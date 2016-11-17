# TODO: slew mode 2 actually has a bug: it computes target - value as signed
# 32-bit integer and uses that to determine the slew step.  This means that
# e.g. slewing from -0x7fffffff to 1 will actually down-slew and underflow the
# value.  This bug is not yet simulated.  Note that slew modes 0 and 1 do not
# suffer from this problem.


def ocabs( n ):
    """One's complement absolute value"""
    if n < 0:
        n = ~n
    return n


# build lookup table for linear slew values
linear_slew = [ round( 0x4000 * 10**(.5 - .1*rate) )  for rate in range(16) ]


def exp_slew( rate, delta ):
    """Helper for computing exponential and constant-dB slew"""

    # bits 0-1 of rate select factor from [1.5, 1.25, 1.125, 1.0]
    tmp = (rate + 1) & 3;
    if tmp != 0:
        delta += delta >> tmp;

    # bits 2-5 of rate determine power-of-two scale factor
    delta >>= 4 + rate // 4

    # make sure delta is never zero.  note that this can only happen when
    # slewing up since delta is and remains negative when slewing down.
    if delta == 0:
        delta = 1
    return delta


def slew_up( curve, rate, current, target ):
    if curve == 0:
        current += linear_slew[ rate & 15 ]
    elif curve == 1:
        current += exp_slew( rate, ocabs(current) )
    elif curve == 2:
        current += exp_slew( rate, target - current )
        # ew... why?
        if current > target - 10:
            return target
    else:
        return target

    if current > target:
        return target

    return current


def slew_down( curve, rate, current, target ):
    if curve == 0:
        current -= linear_slew[ rate & 15 ]
    elif curve == 1:
        current += exp_slew( rate, ~ocabs(current) )
    elif curve == 2:
        current += exp_slew( rate, target - current )
    else:
        return target

    if current < target:
        return target

    return current


def slew( mode, current, target ):
    """Simulate Sigma300 slew peripheral"""

    if target < current:
        curve = (mode >>  0) &  3
        rate  = (mode >>  4) & 63
        return slew_down( curve, rate, current, target )

    elif target > current:
        curve = (mode >>  2) &  3
        rate  = (mode >> 10) & 63
        return slew_up( curve, rate, current, target )

    else:
        return current


def print_slew( curve, rate, current, target ):
    print( current )

    if target < current:
        f = slew_down
    else:
        f = slew_up

    while target != current:
        current = f( curve, rate, current, target )
        print( current )
