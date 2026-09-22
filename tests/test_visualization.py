import helpers  # noqa: F401

import hst_constants as C
import hst_evaluation as E
import hst_visualization as V


def test_yard_figure_builds_and_locks_axes():
    occ = (( 0, 1), (), (2,))
    fig = V.yard_figure(3, 2, occ, "Test")
    assert fig.layout.xaxis.fixedrange is True
    assert fig.layout.yaxis.fixedrange is True


def test_h_curve_figure_builds():
    p = E.Params(rows=8, depth=2, n_items=30, window=8, dwell=80, sigma=0)
    points = E.h_curve(p.rows, p.depth, p.n_items, p.window, p.dwell, p.sigma, n_trials=20)
    fig = V.h_curve_figure(points)
    assert len(fig.data) == 2
    assert fig.layout.xaxis.fixedrange is True


def test_sigma_curve_figure_builds():
    p = E.Params(rows=8, depth=2, n_items=30, window=8, dwell=80, sigma=0)
    points = E.sigma_curve(p.rows, p.depth, p.n_items, p.window, p.dwell, n_trials=20)
    fig = V.sigma_curve_figure(points)
    assert len(fig.data) == 2


def test_comparison_figure_builds():
    p = E.Params(rows=8, depth=2, n_items=30, window=8, dwell=80, sigma=0)
    res_n, res_l = E.run_one(p, seed=1)
    fig = V.comparison_figure(res_n, res_l)
    assert len(fig.data) == 2
    assert len(fig.data[0].x) == 4
