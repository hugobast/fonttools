"""fontTools.misc.bezierTools.py -- tools for working with bezier path segments."""


__all__ = ["calcQuadraticBounds", "calcCubicBounds", "splitLine", "splitQuadratic",
	"splitCubic", "solveQuadratic", "solveCubic"]


from fontTools.misc.arrayTools import calcBounds
import Numeric


def calcQuadraticBounds(pt1, pt2, pt3):
	"""Return the bounding rectangle for a qudratic bezier segment.
	pt1 and pt3 are the "anchor" points, pt2 is the "handle"."""
	# convert points to Numeric arrays
	pt1, pt2, pt3 = Numeric.array((pt1, pt2, pt3))

	# calc quadratic parameters
	c = pt1
	b = (pt2 - c) * 2.0
	a = pt3 - c - b

	# calc first derivative
	ax, ay = a * 2
	bx, by = b
	roots = []
	if ax != 0:
		roots.append(-bx/ax)
	if ay != 0:
		roots.append(-by/ay)
	points = [a*t*t + b*t + c for t in roots if 0 <= t < 1] + [pt1, pt3]
	return calcBounds(points)


def calcCubicBounds(pt1, pt2, pt3, pt4):
	"""Return the bounding rectangle for a cubic bezier segment.
	pt1 and pt4 are the "anchor" points, pt2 and pt3 are the "handles"."""
	# convert points to Numeric arrays
	pt1, pt2, pt3, pt4 = Numeric.array((pt1, pt2, pt3, pt4))
	
	# calc cubic parameters
	d = pt1
	c = (pt2 - d) * 3.0
	b = (pt3 - pt2) * 3.0 - c
	a = pt4 - d - c - b
	
	# calc first derivative
	ax, ay = a * 3.0
	bx, by = b * 2.0
	cx, cy = c
	xRoots = [t for t in solveQuadratic(ax, bx, cx) if 0 <= t < 1]
	yRoots = [t for t in solveQuadratic(ay, by, cy) if 0 <= t < 1]
	roots = xRoots + yRoots
	
	points = [(a*t*t*t + b*t*t + c * t + d) for t in roots] + [pt1, pt4]
	return calcBounds(points)


def splitLine(pt1, pt2, where, isHorizontal):
	"""Split the line between pt1 and pt2 at position 'where', which
	is an x coordinate if isHorizontal is False, a y coordinate if
	isHorizontal is True. Return a list of two line segments if the
	line was successfully split, or a list containing the original
	line."""
	pt1, pt2 = Numeric.array((pt1, pt2))
	a = (pt2 - pt1)
	b = pt1
	ax = a[isHorizontal]
	if ax == 0:
		return [(pt1, pt2)]
	t = float(where - b[isHorizontal]) / ax
	midPt = a * t + b
	return [(pt1, midPt), (midPt, pt2)]


def splitQuadratic(pt1, pt2, pt3, where, isHorizontal):
	"""Split the quadratic curve between pt1, pt2 and pt3 at position 'where',
	which is an x coordinate if isHorizontal is False, a y coordinate if
	isHorizontal is True. Return a list of curve segments."""
	pt1, pt2, pt3 = Numeric.array((pt1, pt2, pt3))
	c = pt1
	b = (pt2 - c) * 2.0
	a = pt3 - c - b
	solutions = solveQuadratic(a[isHorizontal], b[isHorizontal],
		c[isHorizontal] - where)
	solutions = [t for t in solutions if 0 <= t < 1]
	solutions.sort()
	if not solutions:
		return [(pt1, pt2, pt3)]
	
	segments = []
	solutions.insert(0, 0.0)
	solutions.append(1.0)
	for i in range(len(solutions) - 1):
		t1 = solutions[i]
		t2 = solutions[i+1]
		delta = (t2 - t1)
		# calc new a, b and c
		a1 = a * delta**2
		b1 = (2*a*t1 + b) * delta
		c1 = a*t1**2 + b*t1 + c
		# calc new points
		pt1 = c1
		pt2 = (b1 * 0.5) + c1
		pt3 = a1 + b1 + c1
		segments.append((pt1, pt2, pt3))
	return segments


def splitCubic(pt1, pt2, pt3, pt4, where, isHorizontal):
	"""Split the cubic curve between pt1, pt2, pt3 and pt4 at position 'where',
	which is an x coordinate if isHorizontal is False, a y coordinate if
	isHorizontal is True. Return a list of curve segments."""
	pt1, pt2, pt3, pt4 = Numeric.array((pt1, pt2, pt3, pt4))
	d = pt1
	c = (pt2 - d) * 3.0
	b = (pt3 - pt2) * 3.0 - c
	a = pt4 - d - c - b
	
	solutions = solveCubic(a[isHorizontal], b[isHorizontal], c[isHorizontal],
		d[isHorizontal] - where)
	solutions = [t for t in solutions if 0 <= t < 1]
	solutions.sort()
	if not solutions:
		return [(pt1, pt2, pt3, pt4)]
	
	segments = []
	solutions.insert(0, 0.0)
	solutions.append(1.0)
	for i in range(len(solutions) - 1):
		t1 = solutions[i]
		t2 = solutions[i+1]
		delta = (t2 - t1)
		# calc new a, b, c and d
		a1 = a * delta**3
		b1 = (3*a*t1 + b) * delta**2
		c1 = (2*b*t1 + c + 3*a*t1**2) * delta
		d1 = a*t1**3 + b*t1**2 + c*t1 + d
		# calc new points
		pt1 = d1
		pt2 = (c1 / 3.0) + d1
		pt3 = (b1 + c1) / 3.0 + pt2
		pt4 = a1 + d1 + c1 + b1
		segments.append((pt1, pt2, pt3, pt4))
	return segments


#
# Equation solvers.
#

from math import sqrt, acos, cos, pi


def solveQuadratic(a, b, c,
		sqrt=sqrt):
	"""Solve a quadratic equation where a, b and c are real.
	    a*x*x + b*x + c = 0
	This function returns a list of roots.
	"""
	if a == 0.0:
		if b == 0.0:
			# We have a non-equation; therefore, we have no valid solution
			roots = []
		else:
			# We have a linear equation with 1 root.
			roots = [-c/b]
	else:
		# We have a true quadratic equation.  Apply the quadratic formula to find two roots.
		DD = b*b - 4.0*a*c
		if DD >= 0.0:
			roots = [(-b+sqrt(DD))/2.0/a, (-b-sqrt(DD))/2.0/a]
		else:
			# complex roots, ignore
			roots = []
	return roots


def solveCubic(a, b, c, d,
		abs=abs, pow=pow, sqrt=sqrt, cos=cos, acos=acos, pi=pi):
	"""Solve a cubic equation where a, b, c and d are real.
	    a*x*x*x + b*x*x + c*x + d = 0
	This function returns a list of roots.
	"""
	#
	# adapted from:
	#   CUBIC.C - Solve a cubic polynomial
	#   public domain by Ross Cottrell
	# found at: http://www.strangecreations.com/library/snippets/Cubic.C
	#
	if abs(a) < 1e-6:
		# don't just test for zero; for very small values of 'a' solveCubic()
		# returns unreliable results, so we fall back to quad.
		return solveQuadratic(b, c, d)
	a1 = b/a
	a2 = c/a
	a3 = d/a
	
	Q = (a1*a1 - 3.0*a2)/9.0
	R = (2.0*a1*a1*a1 - 9.0*a1*a2 + 27.0*a3)/54.0
	R2_Q3 = R*R - Q*Q*Q

	if R2_Q3 <= 0:
		theta = acos(R/sqrt(Q*Q*Q))
		x0 = -2.0*sqrt(Q)*cos(theta/3.0) - a1/3.0
		x1 = -2.0*sqrt(Q)*cos((theta+2.0*pi)/3.0) - a1/3.0
		x2 = -2.0*sqrt(Q)*cos((theta+4.0*pi)/3.0) - a1/3.0
		return [x0, x1, x2]
	else:
		x = pow(sqrt(R2_Q3)+abs(R), 1/3.0)
		x = x + Q/x
		if R >= 0.0:
			x = -x
		x = x - a1/3.0
		return [x]
