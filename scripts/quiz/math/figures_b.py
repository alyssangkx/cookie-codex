"""Figures for group B (algebra): triangle and rectangle with side expressions."""
from figures import Fig


def triangle_labels(l1, l2, l3, title="Triangle with sides marked in terms of x"):
    """Triangle ABC, labels on AB (bottom), BC (right) and CA (left). Not drawn to scale."""
    f = Fig(340, 190)
    A, B, C = (70, 150), (280, 150), (150, 30)
    f.poly([A, B, C], shade=0.06)
    cen = ((A[0] + B[0] + C[0]) / 3, (A[1] + B[1] + C[1]) / 3)
    f.side_label(A, B, l1, offset=16, inside=cen)
    f.side_label(B, C, l2, offset=34, inside=cen)
    f.side_label(C, A, l3, offset=34, inside=cen)
    return f.svg(title)


def rectangle_labels(length, width, title="Rectangle with sides marked in terms of x"):
    f = Fig(300, 180)
    x0, y0, w, h = 100, 40, 170, 100
    f.rect(x0, y0, w, h, shade=0.06)
    f.text(x0 + w / 2, y0 - 14, length, size=13)
    f.text(x0 - 8, y0 + h / 2, width, anchor="end", size=13)
    return f.svg(title)
