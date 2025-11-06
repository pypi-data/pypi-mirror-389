from sympy import symbols, simplify
from symbolic_extensions import scaffold, mollify, jacobian, implicit_diff, symbolic_kernel

x, y = symbols('x y')

def test_scaffold():
    result = scaffold([x**2 + x, x**2 - x])[0]
    assert simplify(result - (x**2 + x)) == 0

def test_mollify():
    result = mollify(x**2 + x, 3)
    assert result.as_poly().degree() == 2

def test_jacobian():
    J = jacobian([x**2 + y, x*y], [x, y])
    assert J.shape == (2, 2)

def test_implicit():
    F = x**2 + y**2 - 1
    result = implicit_diff(F)
    assert result.free_symbols.issubset({x, y})

def test_kernel():
    k = symbolic_kernel(x**2 + 1, x**2 + x)
    assert k.is_number or k.is_real


if __name__ == "__main__":
    test_scaffold()
    test_mollify()
    test_jacobian()
    test_implicit()
    test_kernel()
    print("✅ All symbolic extension tests passed.")
