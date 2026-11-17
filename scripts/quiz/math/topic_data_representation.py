"""Data representation and interpretation: picture graphs, bar graphs, tables, line graphs, pie charts.

Every question carries a figure. The numbers the student must read are only in the figure, never in the stem
(totals, prices and counts that tie a pie fraction to an amount are problem data, not graph readings).
"""
from common import *
from figures import bar_chart, line_graph
from figures_E import picture_graph, table_fig, pie_fig

T = "math-data-representation-and-interpretation"
O = T + "-picture-graphs-bar-graphs-tables-line-graphs-and-pie-charts-"
PIC1, PIC2, BAR, SCALE, TABLE, MIX = (O + f"0{i}" for i in range(1, 7))

num = lambda x: str(int(x))
pct = lambda x: f"{int(x)}%"

# ---------------------------------------------------------------- contexts

CAT = [
    dict(cats=["Apple", "Banana", "Orange", "Mango", "Grape", "Papaya"], title="Favourite fruit", yl="Number of pupils",
         intro="the number of pupils who chose each fruit as their favourite",
         one="How many pupils chose {a}?", diff="How many more pupils chose {a} than {b}?",
         tot="How many pupils chose {a} or {b}?", pctq="What percentage of the pupils chose {a}?",
         pie="the favourite fruit of {N} pupils", noun="pupils", sing="pupil", sell=None),
    dict(cats=["Bus", "MRT", "Car", "Walk", "Bicycle", "Taxi"], title="How pupils travel", yl="Number of pupils",
         intro="the number of pupils who travel to school by each mode of transport",
         one="How many pupils travel to school by {a}?", diff="How many more pupils travel to school by {a} than by {b}?",
         tot="How many pupils travel to school by {a} or {b}?", pctq="What percentage of the pupils travel to school by {a}?",
         pie="how {N} pupils travel to school", noun="pupils", sing="pupil", sell=None),
    dict(cats=["Chess", "Choir", "Drama", "Band", "Scouts", "Art"], title="CCA membership", yl="Number of pupils",
         intro="the number of pupils in each CCA",
         one="How many pupils are in {a}?", diff="How many more pupils are in {a} than in {b}?",
         tot="How many pupils are in {a} and {b} altogether?", pctq="What percentage of the pupils are in {a}?",
         pie="the CCAs joined by {N} pupils", noun="pupils", sing="pupil", sell=None),
    dict(cats=["Comics", "Fiction", "Science", "Sports", "Poetry", "History"], title="Library books borrowed", yl="Number of books",
         intro="the number of library books of each type that were borrowed in a week",
         one="How many {a} books were borrowed?", diff="How many more {a} books than {b} books were borrowed?",
         tot="How many {a} and {b} books were borrowed altogether?", pctq="What percentage of the books borrowed were {a} books?",
         pie="the types of {N} library books borrowed in a week", noun="books", sing="book", sell=None),
    dict(cats=["Vanilla", "Mango", "Mint", "Coffee", "Durian", "Cocoa"], title="Ice cream sold", yl="Number of scoops",
         intro="the number of scoops of each ice cream flavour sold in a day",
         one="How many scoops of {a} were sold?", diff="How many more scoops of {a} than {b} were sold?",
         tot="How many scoops of {a} and {b} were sold altogether?", pctq="What percentage of the scoops sold were {a}?",
         pie="the flavours of {N} scoops of ice cream sold in a day", noun="scoops", sing="scoop",
         sell=("Each scoop costs ${p}.", [2, 3, 4])),
    dict(cats=["Paper", "Plastic", "Glass", "Metal", "Cans", "Cloth"], title="Recycling collected", yl="Mass in kg",
         intro="the mass of each type of recycling collected at a school",
         one="How many kg of {a} were collected?", diff="How many more kg of {a} than {b} were collected?",
         tot="How many kg of {a} and {b} were collected altogether?", pctq="What percentage of the recycling collected was {a}?",
         pie="the types of {N} kg of recycling collected at a school", noun="kg", sing="kg", sell=None),
    dict(cats=["Laksa", "Prata", "Satay", "Rice", "Noodle", "Soup"], title="Food stall sales", yl="Portions sold",
         intro="the number of portions of each dish sold at a food stall",
         one="How many portions of {a} were sold?", diff="How many more portions of {a} than {b} were sold?",
         tot="How many portions of {a} and {b} were sold altogether?", pctq="What percentage of the portions sold were {a}?",
         pie="the dishes in {N} portions sold at a food stall", noun="portions", sing="portion",
         sell=("Each portion costs ${p}.", [3, 4, 5, 6])),
    dict(cats=["Fish", "Cat", "Dog", "Bird", "Rabbit", "Hamster"], title="Pets kept", yl="Number of pupils",
         intro="the number of pupils who keep each type of pet",
         one="How many pupils keep {a}?", diff="How many more pupils keep {a} than {b}?",
         tot="How many pupils keep {a} or {b}?", pctq="What percentage of the pupils keep {a}?",
         pie="the pets kept by {N} pupils", noun="pupils", sing="pupil", sell=None),
    dict(cats=["Choc", "Mocha", "Lemon", "Berry", "Cheese", "Honey"], title="Cupcakes sold", yl="Number of cupcakes",
         intro="the number of cupcakes of each flavour sold at a bake sale",
         one="How many {a} cupcakes were sold?", diff="How many more {a} cupcakes than {b} cupcakes were sold?",
         tot="How many {a} and {b} cupcakes were sold altogether?", pctq="What percentage of the cupcakes sold were {a}?",
         pie="the flavours of {N} cupcakes sold at a bake sale", noun="cupcakes", sing="cupcake",
         sell=("Each cupcake costs ${p}.", [2, 3, 4, 5])),
]

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
TIME = [
    dict(cats=DAYS, seq=True, title="Library visitors", yl="Number of visitors", per="day",
         intro="the number of visitors to a library on each day",
         one="How many visitors came on {a}?", diff="How many more visitors came on {a} than on {b}?",
         tot="How many visitors came on {a} and {b} altogether?", avg="the average number of visitors per day", sell=None),
    dict(cats=DAYS, seq=True, title="Bubble tea sold", yl="Number of cups", per="day",
         intro="the number of cups of bubble tea sold at a stall on each day",
         one="How many cups were sold on {a}?", diff="How many more cups were sold on {a} than on {b}?",
         tot="How many cups were sold on {a} and {b} altogether?", avg="the average number of cups sold per day",
         sell=("Each cup of bubble tea costs ${p}.", [3, 4, 5])),
    dict(cats=DAYS, seq=True, title="Concert tickets sold", yl="Number of tickets", per="day",
         intro="the number of tickets sold for a school concert on each day",
         one="How many tickets were sold on {a}?", diff="How many more tickets were sold on {a} than on {b}?",
         tot="How many tickets were sold on {a} and {b} altogether?", avg="the average number of tickets sold per day",
         sell=("Each ticket costs ${p}.", [4, 5, 6, 8])),
    dict(cats=DAYS, seq=True, title="Cars washed", yl="Number of cars", per="day",
         intro="the number of cars washed at a car wash on each day",
         one="How many cars were washed on {a}?", diff="How many more cars were washed on {a} than on {b}?",
         tot="How many cars were washed on {a} and {b} altogether?", avg="the average number of cars washed per day",
         sell=("Each car wash costs ${p}.", [6, 8, 10, 12])),
    dict(cats=MONTHS, seq=True, title="Books sold", yl="Number of books", per="month",
         intro="the number of books sold by a bookshop in each month",
         one="How many books were sold in {a}?", diff="How many more books were sold in {a} than in {b}?",
         tot="How many books were sold in {a} and {b} altogether?", avg="the average number of books sold per month",
         sell=("Each book costs ${p}.", [4, 5, 6, 8])),
    dict(cats=MONTHS, seq=True, title="Monthly rainfall", yl="Rainfall in mm", per="month",
         intro="the rainfall in a town in each month",
         one="How many mm of rain fell in {a}?", diff="How many more mm of rain fell in {a} than in {b}?",
         tot="How many mm of rain fell in {a} and {b} altogether?", avg="the average rainfall per month", sell=None),
]
BARCTX = CAT + TIME
SELL_TIME = [c for c in TIME if c["sell"]]
SELL_CAT = [c for c in CAT if c["sell"]]

STEPS = (2, 4, 5, 10, 20, 25, 50)


def labels_of(r, c, n):
    if c.get("seq"):
        s = r.randint(0, len(c["cats"]) - n)
        return c["cats"][s:s + n]
    return r.sample(c["cats"], n)


def step_vals(r, n, steps=STEPS, kmin=2, kmax=8):
    step = r.choice(steps)
    return step, [k * step for k in r.sample(range(kmin, kmax + 1), n)]


def lead(r, kind, intro):
    return r.choice([f"The {kind} shows {intro}.", f"{r.choice(NAMES)} drew a {kind} to show {intro}.",
                     f"Study the {kind} below. It shows {intro}."])


# ---------------------------------------------------------------- tables

TAB = [
    dict(title="Pupils in four classes", rows=["6A", "6B", "6C", "6D"], cols=["Boys", "Girls"],
         intro="the number of boys and girls in four Primary 6 classes",
         q="How many {coll} are in Class {row}?", rowq="How many pupils are in Class {row}?",
         colq="How many {coll} are there in the four classes altogether?"),
    dict(title="Drinks sold at a kiosk", rows=["Mon", "Tue", "Wed", "Thu"], cols=["Tea", "Coffee", "Milo"],
         intro="the number of cups of each drink sold at a kiosk",
         q="How many cups of {coll} were sold on {row}?", rowq="How many cups were sold on {row}?",
         colq="How many cups of {coll} were sold altogether?"),
    dict(title="Books read", rows="NAMES", cols=["Week 1", "Week 2", "Week 3"],
         intro="the number of books some pupils read over three weeks",
         q="How many books did {row} read in {col}?", rowq="How many books did {row} read in all?",
         colq="How many books were read in {col} altogether?"),
    dict(title="Fruit sold", rows=["Shop A", "Shop B", "Shop C"], cols=["Apples", "Pears", "Oranges"],
         intro="the number of fruits sold at three shops",
         q="How many {coll} did {row} sell?", rowq="How many fruits did {row} sell?",
         colq="How many {coll} were sold altogether?"),
]


def tab_setup(r, minrows=3):
    c = r.choice(TAB)
    rows = r.sample(NAMES, 4) if c["rows"] == "NAMES" else list(c["rows"])
    nr = r.randint(minrows, len(rows))
    rows = rows[:nr]
    nc = len(c["cols"])
    vals = r.sample(range(8, 96), nr * nc)
    grid = [vals[i * nc:(i + 1) * nc] for i in range(nr)]
    return c, rows, grid


def tab_fig(c, rows, grid, total=False):
    return table_fig([""] + c["cols"], [[rw] + [str(v) for v in g] for rw, g in zip(rows, grid)], title=c["title"])


def fmtq(c, tmpl, row=None, col=None):
    return c[tmpl].format(row=row, col=col, coll=(col or "").lower())


# ================================================================ BASIC

@template(T, "basic", PIC1, PIC2)
def picture_read(r):
    """math-pat-table-bar-graph-reading"""
    c = r.choice(CAT)
    n = r.randint(4, 5)
    labs = r.sample(c["cats"], n)
    key = r.choice([1, 2, 4, 5, 10])
    halves = r.sample(range(2, 17), n) if key % 2 == 0 else [2 * x for x in r.sample(range(1, 9), n)]
    counts = [h * key // 2 for h in halves]
    i = r.randrange(n)
    h = halves[i]
    ans = counts[i]
    unit_name = c["noun"] if key > 1 else c["sing"]
    wrong = [(ceil_div(h, 2), "ignored_key", "Counted the symbols but did not multiply by the value of each symbol."),
             (counts[(i + 1) % n], "read_wrong_row", "Read the row next to the one asked about."),
             ((h + 1) // 2 * key if h % 2 else None, "half_symbol_as_full", "Counted the half symbol as a whole symbol."),
             (h // 2 * key if h % 2 else None, "ignored_half_symbol", "Left out the half symbol.")]
    stem = f"{lead(r, 'picture graph', c['intro'])} {c['one'].format(a=labs[i])}"
    return build(picture_read, stem, ans, wrong,
                 [f"Each symbol stands for {key}.", f"{labs[i]} has {plural(f'{h / 2:g}', 'symbol')}.", f"{h / 2:g} x {key} = {ans}"],
                 {"labs": labs, "counts": counts, "key": key, "i": i}, whole=True, unit_size=key,
                 figure=picture_graph(labs, counts, key, unit_name, c["title"]))


def ceil_div(a, b):
    return -(-a // b)


@checker(picture_read)
def _(p):
    # simulate drawing symbols one by one
    c, k = p["counts"][p["i"]], p["key"]
    tot, left = 0, c
    while left > 0:
        if left >= k:
            tot += k
            left -= k
        else:
            tot += left
            left = 0
    return F(tot)


@template(T, "basic", BAR, SCALE)
def bar_read(r):
    """math-pat-table-bar-graph-reading"""
    c = r.choice(BARCTX)
    n = r.randint(5, 6)
    labs = labels_of(r, c, n)
    step, vals = step_vals(r, n)
    i = r.randrange(n)
    stem = f"{lead(r, 'bar graph', c['intro'])} {c['one'].format(a=labs[i])}"
    wrong = [(vals[(i + 1) % n], "read_wrong_bar", "Read the bar next to the one asked about."),
             (vals[i] // step, "read_gridline_count", "Counted gridlines instead of reading the scale."),
             (vals[i - 1], "read_wrong_bar", "Read a different bar.")]
    return build(bar_read, stem, vals[i], wrong,
                 [f"Each gridline is {step}.", f"The top of the {labs[i]} bar is at {vals[i]}."],
                 {"labs": labs, "vals": vals, "i": i}, whole=True, unit_size=step,
                 figure=bar_chart(labs, vals, c["title"], c["yl"], step=step))


@checker(bar_read)
def _(p):
    return F(dict(zip(p["labs"], p["vals"]))[p["labs"][p["i"]]])


@template(T, "basic", BAR, SCALE)
def bar_extreme(r):
    """math-pat-table-bar-graph-reading"""
    c = r.choice(BARCTX)
    n = r.randint(5, 6)
    labs = labels_of(r, c, n)
    step, vals = step_vals(r, n, steps=(5, 10, 20, 25, 50))
    big = r.random() < 0.5
    s = sorted(vals)
    ans = s[-1] if big else s[0]
    word = "greatest" if big else "smallest"
    stem = f"{lead(r, 'bar graph', c['intro'])} What is the {word} number shown on the graph?"
    wrong = [(s[-2] if big else s[1], "second_instead_of_extreme", f"Gave the second {word} bar."),
             (s[0] if big else s[-1], "opposite_extreme", "Gave the opposite extreme."),
             (ans // step, "read_gridline_count", "Counted gridlines instead of reading the scale.")]
    return build(bar_extreme, stem, ans, wrong,
                 [f"Find the {'tallest' if big else 'shortest'} bar.", f"Read its value from the scale: {ans}."],
                 {"vals": vals, "big": big}, whole=True, unit_size=step,
                 figure=bar_chart(labs, vals, c["title"], c["yl"], step=step))


@checker(bar_extreme)
def _(p):
    v = p["vals"]
    return F(next(x for x in v if all(x >= y for y in v)) if p["big"] else next(x for x in v if all(x <= y for y in v)))


@template(T, "basic", TABLE, MIX)
def table_read(r):
    """math-pat-table-bar-graph-reading"""
    c, rows, grid = tab_setup(r)
    ri, ci = r.randrange(len(rows)), r.randrange(len(c["cols"]))
    ans = grid[ri][ci]
    stem = f"{lead(r, 'table', c['intro'])} " + fmtq(c, "q", rows[ri], c["cols"][ci])
    oc = (ci + 1) % len(c["cols"])
    wrong = [(grid[ri][oc], "read_wrong_column", "Read the right row but the wrong column."),
             (grid[(ri + 1) % len(rows)][ci], "read_wrong_row", "Read the right column but the wrong row."),
             (sum(grid[ri]), "added_whole_row", "Added every number in the row."),
             (grid[(ri + 1) % len(rows)][oc], "read_wrong_cell", "Read a cell in the wrong row and column.")]
    return build(table_read, stem, ans, wrong, [f"Find row {rows[ri]} and column {c['cols'][ci]}.", f"The number is {ans}."],
                 {"rows": rows, "grid": grid, "ri": ri, "ci": ci}, whole=True, figure=tab_fig(c, rows, grid))


@checker(table_read)
def _(p):
    return F(next(v for i, rw in enumerate(p["rows"]) for j, v in enumerate(p["grid"][i]) if (i, j) == (p["ri"], p["ci"])))


# ---------------------------------------------------------------- line graphs

LINE = [
    dict(title="Height of a plant (cm)", xs=[1, 2, 3, 4, 5, 6], xlab=lambda x: f"Wk {x}", at=lambda x: f"at the end of Week {x}",
         meas="the height of the plant", intro="the height of a bean plant at the end of each week", pre="", suf=" cm",
         steps=(2, 5), when=lambda V: f"In which week did the plant first reach a height of {V} cm?"),
    dict(title="Savings ($)", xs=[1, 2, 3, 4, 5, 6], xlab=lambda x: MONTHS[x - 1], at=lambda x: f"at the end of {MONTHS[x - 1]}",
         meas="the amount in the savings account", intro="the amount in a savings account at the end of each month",
         pre="$", suf="", steps=(10, 20, 50), when=None),
    dict(title="Temperature (°C)", xs=[8, 9, 10, 11, 12, 13],
         xlab=lambda x: f"{x} am" if x < 12 else f"{12 if x == 12 else x - 12} pm", at=lambda x: "at " + (f"{x} am" if x < 12 else f"{12 if x == 12 else x - 12} pm"),
         meas="the temperature", intro="the temperature in a park at each hour", pre="", suf="°C", steps=(4, 5), when=None),
    dict(title="Visitors at the fair", xs=[10, 11, 12, 13, 14, 15],
         xlab=lambda x: f"{x} am" if x < 12 else f"{12 if x == 12 else x - 12} pm", at=lambda x: "at " + (f"{x} am" if x < 12 else f"{12 if x == 12 else x - 12} pm"),
         meas="the number of visitors at the fair", intro="the number of visitors at a fair at each hour", pre="", suf="",
         steps=(20, 50), when=None),
    dict(title="Water in tank (litres) vs minutes", xs=[0, 5, 10, 15, 20, 25, 30], xlab=str,
         at=lambda x: f"after {x} minutes", meas="the volume of water in the tank", intro="the volume of water in a tank over 30 minutes",
         pre="", suf=" litres", steps=(10, 20),
         when=lambda V: f"After how many minutes did the tank first hold {V} litres of water?"),
]
RATE = [
    dict(title="Water in tank (litres) vs minutes", intro="the volume of water in a tank", flow="water flowed into the tank", up=True),
    dict(title="Water in pool (litres) vs minutes", intro="the volume of water in a paddling pool", flow="water flowed into the pool", up=True),
    dict(title="Water in drum (litres) vs minutes", intro="the volume of water in a drum as it is drained", flow="water flowed out of the drum", up=False),
]
MINS = [0, 5, 10, 15, 20, 25, 30]


def lfmt(c):
    return lambda x: f"{c['pre']}{int(x)}{c['suf']}"


def line_ks(r, c, kind):
    n = len(c["xs"])
    ks = r.sample(range(1, 9), n)
    return sorted(ks) if kind == "up" else ks


@template(T, "basic", MIX)
def line_read(r):
    """math-pat-table-bar-graph-reading"""
    c = r.choice(LINE)
    step = r.choice(c["steps"])
    ks = line_ks(r, c, r.choice(["up", "wiggle"]))
    vals = [k * step for k in ks]
    i = r.randrange(len(vals))
    stem = f"{lead(r, 'line graph', c['intro'])} What was {c['meas']} {c['at'](c['xs'][i])}?"
    wrong = [(vals[min(i + 1, len(vals) - 1)] if i + 1 < len(vals) else vals[i - 1], "read_wrong_point", "Read the next point on the line."),
             (vals[i - 1] if i else vals[1], "read_wrong_point", "Read the previous point on the line."),
             (ks[i], "read_gridline_count", "Counted gridlines instead of reading the scale.")]
    return build(line_read, stem, vals[i], wrong, [f"Find {c['at'](c['xs'][i])} on the horizontal axis and go up to the line.",
                 f"Read across to the scale: {vals[i]}."], {"vals": vals, "i": i}, show=lfmt(c), whole=True, unit_size=step,
                 figure=line_graph([c["xlab"](x) for x in c["xs"]], vals, c["title"], step=step))


@checker(line_read)
def _(p):
    return F(dict(enumerate(p["vals"]))[p["i"]])


def pie_pcts(r, n):
    while True:
        cuts = sorted(r.sample(range(1, 20), n - 1))
        parts = [(b - a) * 5 for a, b in zip([0] + cuts, cuts + [20])]
        if min(parts) >= 15:
            return parts


FRAC_OK = {10, 20, 25, 30, 40, 50, 60, 70, 75, 80}


def plab(p, as_frac):
    return frac(F(p, 100)) if as_frac else f"{p}%"


@template(T, "basic", MIX)
def pie_basic(r):
    """math-pat-table-bar-graph-reading"""
    c = r.choice(CAT)
    n = 3
    labs = r.sample(c["cats"], n)
    while True:
        parts = pie_pcts(r, n)
        if all(p in FRAC_OK for p in parts):
            break
    as_frac = r.random() < 0.5
    ai = r.randrange(n)
    shows = [None if i == ai else plab(p, as_frac) for i, p in enumerate(parts)]
    q = c["pctq"].format(a=labs[ai])
    if as_frac:
        q = q.replace("What percentage", "What fraction")
    show = (lambda x: frac(x)) if as_frac else pct
    ans = F(parts[ai], 100) if as_frac else parts[ai]
    others = sum(p for i, p in enumerate(parts) if i != ai)
    big = max(p for i, p in enumerate(parts) if i != ai)
    cv = (lambda p: F(p, 100)) if as_frac else (lambda p: p)
    wrong = [(cv(others), "added_given_sectors", "Added the labelled sectors and stopped."),
             (cv(100 - big), "subtracted_only_one_sector", "Took away only one of the labelled sectors from the whole."),
             (cv(abs(parts[ai - 1] - parts[ai - 2])), "difference_of_sectors", "Found the difference of the labelled sectors.")]
    stem = f"The pie chart shows {c['pie'].format(N='some')}. {q}"
    return build(pie_basic, stem, ans, wrong,
                 ["The whole pie is 100% (or 1).", f"Take away the labelled sectors: 100 - {others} = {100 - others}."],
                 {"parts": parts, "ai": ai, "frac": as_frac}, show=show, whole=not as_frac,
                 figure=pie_fig(labs, parts, shows, c["title"]))


@checker(pie_basic)
def _(p):
    # the three sectors turn through 360 degrees: find the angle of the missing sector, then convert back
    deg = 360 - sum(x * 360 // 100 for i, x in enumerate(p["parts"]) if i != p["ai"])
    return F(deg, 360) if p["frac"] else F(deg * 100, 360)


# ================================================================ INTERMEDIATE

@template(T, "intermediate", BAR, SCALE)
def bar_diff(r):
    """math-pat-table-bar-graph-reading"""
    c = r.choice(BARCTX)
    n = r.randint(5, 6)
    labs = labels_of(r, c, n)
    step, vals = step_vals(r, n)
    i, j = r.sample(range(n), 2)
    if vals[i] < vals[j]:
        i, j = j, i
    a, b = labs[i], labs[j]
    stem = f"{lead(r, 'bar graph', c['intro'])} {c['diff'].format(a=a, b=b)}"
    d = vals[i] - vals[j]
    k = (i + 1) % n
    wrong = [(vals[i] + vals[j], "added_instead_of_subtracting", "Added the two bars instead of finding the difference."),
             (abs(vals[k] - vals[j]) if k != j else None, "read_wrong_bar", "Used the wrong bar for the larger value."),
             (d // step, "read_gridline_count", "Counted the gridlines between the bars, not their values.")]
    return build(bar_diff, stem, d, wrong, [f"{a}: {vals[i]}, {b}: {vals[j]}.", f"{vals[i]} - {vals[j]} = {d}"],
                 {"va": vals[i], "vb": vals[j], "labs": labs, "vals": vals}, whole=True, unit_size=step,
                 figure=bar_chart(labs, vals, c["title"], c["yl"], step=step))


@checker(bar_diff)
def _(p):
    return F(sum(abs(x - y) for x, y in [(p["va"], p["vb"])]))


@template(T, "intermediate", BAR, SCALE)
def bar_total_two(r):
    """math-pat-table-bar-graph-reading"""
    c = r.choice(BARCTX)
    n = r.randint(5, 6)
    labs = labels_of(r, c, n)
    step, vals = step_vals(r, n)
    i, j = r.sample(range(n), 2)
    stem = f"{lead(r, 'bar graph', c['intro'])} {c['tot'].format(a=labs[i], b=labs[j])}"
    t = vals[i] + vals[j]
    k = next(x for x in range(n) if x not in (i, j))
    wrong = [(abs(vals[i] - vals[j]), "subtracted_instead_of_adding", "Found the difference instead of the total."),
             (vals[i] + vals[k], "read_wrong_bar", "Added a bar that was not asked for."),
             (sum(vals), "added_all_bars", "Added every bar.")]
    return build(bar_total_two, stem, t, wrong, [f"{labs[i]}: {vals[i]}, {labs[j]}: {vals[j]}.", f"{vals[i]} + {vals[j]} = {t}"],
                 {"vals": vals, "i": i, "j": j}, whole=True, unit_size=step,
                 figure=bar_chart(labs, vals, c["title"], c["yl"], step=step))


@checker(bar_total_two)
def _(p):
    return F(sum(v for k, v in enumerate(p["vals"]) if k in (p["i"], p["j"])))


@template(T, "intermediate", PIC2, PIC1)
def picture_total(r):
    """math-pat-table-bar-graph-reading"""
    c = r.choice(CAT)
    n = r.randint(4, 5)
    labs = r.sample(c["cats"], n)
    key = r.choice([2, 4, 5, 10])
    halves = r.sample(range(2, 15), n) if key % 2 == 0 else r.sample(range(2, 15, 2), n)  # whole counts only
    counts = [h * key // 2 for h in halves]
    mode = r.choice(["tot", "diff"])
    i, j = r.sample(range(n), 2)
    if mode == "diff" and counts[i] < counts[j]:
        i, j = j, i
    q = c["tot" if mode == "tot" else "diff"].format(a=labs[i], b=labs[j])
    ans = counts[i] + counts[j] if mode == "tot" else counts[i] - counts[j]
    sym = halves[i] / 2, halves[j] / 2
    nosym = sym[0] + sym[1] if mode == "tot" else sym[0] - sym[1]
    wrong = [(nosym, "ignored_key", "Combined the symbols but did not multiply by the value of one symbol."),
             (counts[i] - counts[j] if mode == "tot" else counts[i] + counts[j], "wrong_operation",
              "Used the wrong operation for the question."),
             (counts[i], "used_one_row_only", "Used only one row.")]
    return build(picture_total, f"{lead(r, 'picture graph', c['intro'])} {q}", ans, wrong,
                 [f"Each symbol is {key}.", f"{labs[i]}: {counts[i]}, {labs[j]}: {counts[j]}.", f"Answer: {ans}"],
                 {"counts": counts, "i": i, "j": j, "mode": mode}, whole=True, unit_size=key,
                 figure=picture_graph(labs, counts, key, c["noun"], c["title"]))


@checker(picture_total)
def _(p):
    a, b = p["counts"][p["i"]], p["counts"][p["j"]]
    return F(a + b) if p["mode"] == "tot" else F(max(a, b) - min(a, b))


@template(T, "intermediate", TABLE, MIX)
def table_total(r):
    """math-pat-table-bar-graph-reading"""
    c, rows, grid = tab_setup(r)
    nr, nc = len(rows), len(c["cols"])
    mode = r.choice(["row", "col"])
    if mode == "row":
        i = r.randrange(nr)
        q, ans = fmtq(c, "rowq", rows[i]), sum(grid[i])
        wrong = [(sum(grid[i][:-1]), "left_out_a_cell", "Left out one number in the row."),
                 (sum(g[0] for g in grid), "added_column_instead", "Added a column instead of the row."),
                 (max(grid[i]) - min(grid[i]), "difference_instead_of_total", "Found a difference instead of the total.")]
        pr = {"mode": mode, "i": i}
    else:
        j = r.randrange(nc)
        q, ans = fmtq(c, "colq", None, c["cols"][j]), sum(g[j] for g in grid)
        wrong = [(sum(g[j] for g in grid[:-1]), "left_out_a_row", "Left out one row."),
                 (sum(grid[0]), "added_row_instead", "Added a row instead of the column."),
                 (sum(sum(g) for g in grid), "added_whole_table", "Added every number in the table.")]
        pr = {"mode": mode, "j": j}
    return build(table_total, f"{lead(r, 'table', c['intro'])} {q}", ans, wrong,
                 ["Add the numbers that match the question.", f"Total = {ans}"],
                 {**pr, "grid": grid}, whole=True, figure=tab_fig(c, rows, grid))


@checker(table_total)
def _(p):
    g = p["grid"]
    if p["mode"] == "row":
        return F(0 + sum(g[p["i"]]))
    return F(sum(list(zip(*g))[p["j"]]))


@template(T, "intermediate", MIX, BAR)
def line_change(r):
    """math-pat-table-bar-graph-reading"""
    c = r.choice(LINE)
    step = r.choice(c["steps"])
    ks = line_ks(r, c, r.choice(["up", "wiggle"]))
    vals = [k * step for k in ks]
    n = len(vals)
    i, j = sorted(r.sample(range(n), 2))
    d = abs(vals[j] - vals[i])
    stem = (f"{lead(r, 'line graph', c['intro'])} What was the difference between {c['meas']} "
            f"{c['at'](c['xs'][i])} and {c['at'](c['xs'][j])}?")
    k = j - 1 if j - 1 != i else min(j + 1, n - 1)
    wrong = [(vals[i] + vals[j], "added_instead_of_difference", "Added the two readings."),
             (abs(vals[k] - vals[i]), "read_wrong_point", "Used a neighbouring point for one reading."),
             (max(vals[i], vals[j]), "gave_larger_reading", "Gave the larger reading and did not subtract.")]
    return build(line_change, stem, d, wrong, [f"Readings: {vals[i]} and {vals[j]}.", f"Difference = {d}"],
                 {"vals": vals, "i": i, "j": j}, show=lfmt(c), whole=True, unit_size=step,
                 figure=line_graph([c["xlab"](x) for x in c["xs"]], vals, c["title"], step=step))


@checker(line_change)
def _(p):
    return F(abs(p["vals"][p["i"]] - p["vals"][p["j"]]))


def rate_series(r, up):
    """Seven points 0..30 min made of three straight pieces, each over two intervals."""
    while True:
        k0 = r.randint(1, 3) if up else r.randint(5, 8)
        ds = [r.choice([0, 1, 2, 3]) * (1 if up else -1) for _ in range(3)]
        ks = [k0]
        for d in ds:
            ks += [ks[-1] + d, ks[-1] + 2 * d]
        if min(ks) >= 0 and max(ks) <= 8 and sum(1 for d in ds if d) >= 2 and (up or ks[-1] >= 0):
            return ks, ds


@template(T, "intermediate", MIX)
def line_rate(r):
    """math-pat-line-graph-rate-and-time"""
    c = r.choice(RATE)
    ks, ds = rate_series(r, c["up"])
    step = r.choice([10, 20, 25])
    vals = [k * step for k in ks]
    p = r.choice([q for q in range(3) if ds[q]])
    t1, t2 = MINS[2 * p], MINS[2 * p + 2]
    rate = abs(ds[p]) * step // 5
    stem = (f"{lead(r, 'line graph', c['intro'])} Between {t1} and {t2} minutes, {c['flow']} at a steady rate. "
            "Find this rate in litres per minute.")
    chg = abs(ds[p]) * 2 * step
    wrong = [(chg, "forgot_to_divide_by_time", "Gave the change in volume and did not divide by the time."),
             (abs(ds[p]) * step, "used_one_interval", "Used the change over only one interval of 5 minutes."),
             (rate + 1, "slip_in_division", "Slip in the division."),
             (max(rate - 1, 0) or None, "slip_in_division", "Slip in the division.")]
    return build(line_rate, stem, rate, wrong,
                 [f"At {t1} min: {vals[2 * p]} L; at {t2} min: {vals[2 * p + 2]} L.", f"Change = {chg} L in {t2 - t1} min.",
                  f"Rate = {chg} / {t2 - t1} = {rate} L per minute"],
                 {"v1": vals[2 * p], "v2": vals[2 * p + 2], "t1": t1, "t2": t2}, whole=True,
                 figure=line_graph([str(x) for x in MINS], vals, c["title"], step=step))


@checker(line_rate)
def _(p):
    # rate by simulation: total volume moved divided by number of whole minutes
    litres = abs(p["v2"] - p["v1"])
    mins = len(range(p["t1"], p["t2"]))
    return F(litres, mins)


@template(T, "intermediate", MIX)
def line_reach(r):
    """math-pat-line-graph-rate-and-time"""
    c = r.choice([l for l in LINE if l["when"]])
    step = r.choice(c["steps"])
    ks = line_ks(r, c, "up")
    vals = [k * step for k in ks]
    j = r.randint(1, len(vals) - 1)
    stem = f"{lead(r, 'line graph', c['intro'])} {c['when'](vals[j])}"
    xs = c["xs"]
    wrong = [(xs[j + 1] if j + 1 < len(xs) else xs[j - 1], "read_neighbouring_point", "Gave the next reading time."),
             (xs[j - 1] if xs[j - 1] else xs[j] + 1, "read_neighbouring_point", "Gave the previous reading time."),
             (ks[j], "gave_gridline_count", "Counted gridlines instead of reading the time."),
             (vals[j], "gave_volume_not_time", "Gave the value on the vertical axis instead of the time.")]
    return build(line_reach, stem, xs[j], wrong,
                 [f"Find {vals[j]} on the vertical axis and go across to the line.", f"Read the time below: {xs[j]}."],
                 {"vals": vals, "xs": xs, "target": vals[j]}, whole=True,
                 figure=line_graph([c["xlab"](x) for x in xs], vals, c["title"], step=step))


@checker(line_reach)
def _(p):
    return F(next(x for x, v in zip(p["xs"], p["vals"]) if v == p["target"]))


@template(T, "intermediate", MIX)
def pie_amount(r):
    """math-pat-table-bar-graph-reading math-pat-pie-chart-reading"""
    c = r.choice(CAT)
    n = 3
    labs = r.sample(c["cats"], n)
    parts = pie_pcts(r, n)
    ai = r.randrange(n)
    N = r.choice([100, 120, 160, 200, 240, 300, 400, 500, 600])
    use_f = all(p in FRAC_OK for p in parts) and r.random() < 0.5
    shows = [None if i == ai else plab(p, use_f) for i, p in enumerate(parts)]
    others = sum(p for i, p in enumerate(parts) if i != ai)
    ans = N * parts[ai] // 100
    q = c["one"].format(a=labs[ai])
    stem = f"The pie chart shows {c['pie'].format(N=N)}. {q}"
    big = max(p for i, p in enumerate(parts) if i != ai)
    wrong = [(N * others // 100, "used_labelled_sectors", "Found the amount for the labelled sectors, not the unlabelled one."),
             (parts[ai], "percent_as_amount", "Gave the percentage as the amount."),
             (N * (100 - big) // 100, "subtracted_only_one_sector", "Took away only one labelled sector."),
             (N - ans, "gave_rest", "Gave the amount for all the other sectors.")]
    return build(pie_amount, stem, ans, wrong,
                 [f"Unlabelled sector = 100% - {others}% = {parts[ai]}%.", f"{parts[ai]}% of {N} = {ans}"],
                 {"parts": parts, "ai": ai, "N": N}, whole=True, figure=pie_fig(labs, parts, shows, c["title"]))


@checker(pie_amount)
def _(p):
    # the sector's angle, then its share of the total
    deg = 360 - sum(x * 360 // 100 for i, x in enumerate(p["parts"]) if i != p["ai"])
    return F(p["N"] * deg, 360)


@template(T, "intermediate", BAR, MIX)
def bar_average(r):
    """Average of the bars read from a graph."""
    c = r.choice(TIME)
    n = r.choice([4, 5])
    labs = c["cats"][:n]
    while True:
        step, vals = step_vals(r, n, steps=(2, 4, 5, 10, 20))
        if sum(vals) % n == 0:
            break
    avg = sum(vals) // n
    stem = f"{lead(r, 'bar graph', c['intro'])} Find {c['avg']} over the {n} {c['per']}s shown."
    s = sorted(vals)
    wrong = [(sum(vals), "gave_the_total", "Added the bars but did not divide."),
             (F(sum(vals), n + 1), "wrong_divisor", "Divided by one more than the number of bars."),
             (s[n // 2], "took_middle_bar", "Gave the middle bar instead of the average."),
             (max(vals), "took_largest_bar", "Gave the largest bar.")]
    return build(bar_average, stem, avg, wrong, [f"Total = {sum(vals)}.", f"Average = {sum(vals)} / {n} = {avg}"],
                 {"vals": vals}, whole=True, unit_size=step, figure=bar_chart(labs, vals, c["title"], c["yl"], step=step))


@checker(bar_average)
def _(p):
    v = p["vals"]
    return F(next(a for a in range(0, 10000) if a * len(v) == sum(v)))


@template(T, "intermediate", BAR, MIX)
def avg_missing_bar(r):
    """math-pat-graph-find-missing-from-average"""
    c = r.choice(TIME)
    n = r.choice([4, 5])
    labs = c["cats"][:n]
    while True:
        step, vals = step_vals(r, n, steps=(2, 4, 5, 10, 20))
        if sum(vals) % n == 0:
            break
    m = r.randrange(n)
    avg = sum(vals) // n
    known = sum(vals) - vals[m]
    shown = [0 if k == m else v for k, v in enumerate(vals)]
    stem = (f"{lead(r, 'bar graph', c['intro'])} The bar for {labs[m]} has not been drawn. "
            f"The average over these {n} {c['per']}s was {avg}. Find the value for {labs[m]}.")
    wrong = [(n * avg, "gave_the_total", "Found the total but did not subtract the known bars."),
             ((n - 1) * avg - known, "used_wrong_count", f"Used {n - 1} instead of {n} for the number of {c['per']}s."),
             (avg, "gave_the_average", "Assumed the missing value equals the average."),
             (F(known, n - 1), "average_of_known", "Averaged only the bars that are drawn.")]
    return build(avg_missing_bar, stem, vals[m], wrong,
                 [f"Total = {avg} x {n} = {n * avg}.", f"Known bars add to {known}.", f"{n * avg} - {known} = {vals[m]}"],
                 {"known": known, "avg": avg, "n": n, "shown": shown}, whole=True, unit_size=step,
                 figure=bar_chart(labs, shown, c["title"], c["yl"], step=step))


@checker(avg_missing_bar)
def _(p):
    return F(next(x for x in range(1, 100000) if (p["known"] + x) / p["n"] == p["avg"]))


# ================================================================ COMPETENT

def pie_sectors(r, c, n, need_frac=False):
    labs = r.sample(c["cats"], n)
    while True:
        parts = pie_pcts(r, n)
        if not need_frac or all(p in FRAC_OK for p in parts):
            return labs, parts


@template(T, "competent", MIX)
def pie_compare(r):
    """math-pat-table-bar-graph-reading math-pat-pie-chart-reading"""
    c = r.choice(CAT)
    n = r.choice([4, 5])
    labs, parts = pie_sectors(r, c, n)
    order = sorted(range(n), key=lambda i: -parts[i])
    ai = order[0] if r.random() < 0.6 else order[1]
    bi = r.choice([i for i in range(n) if i != ai and parts[i] < parts[ai]])
    N = r.choice([200, 240, 300, 400, 500, 600, 800])
    use_f = all(p in FRAC_OK for p in parts) and r.random() < 0.5
    shows = [None if i == ai else plab(p, use_f) for i, p in enumerate(parts)]
    others = sum(p for i, p in enumerate(parts) if i != ai)
    ans = N * (parts[ai] - parts[bi]) // 100
    stem = f"The pie chart shows {c['pie'].format(N=N)}. {c['diff'].format(a=labs[ai], b=labs[bi])}"
    skip = next(i for i in range(n) if i not in (ai, bi))
    wrong = [(N * (parts[ai] + parts[bi]) // 100, "added_instead_of_subtracting", "Added the two sectors instead of finding the difference."),
             (parts[ai] - parts[bi], "forgot_total", "Found the difference in percentage and did not apply it to the total."),
             (N * (100 - others + parts[skip] - parts[bi]) // 100, "missed_a_sector", "Left one labelled sector out when finding the unlabelled one."),
             (N * parts[ai] // 100, "used_larger_only", "Gave the amount for the larger sector only.")]
    return build(pie_compare, stem, ans, wrong,
                 [f"{labs[ai]} = 100% - {others}% = {parts[ai]}%.", f"Difference = {parts[ai]}% - {parts[bi]}% = {parts[ai] - parts[bi]}%.",
                  f"{parts[ai] - parts[bi]}% of {N} = {ans}"], {"parts": parts, "ai": ai, "bi": bi, "N": N},
                 whole=True, figure=pie_fig(labs, parts, shows, c["title"]))


@checker(pie_compare)
def _(p):
    deg = [x * 360 // 100 for x in p["parts"]]
    deg[p["ai"]] = 360 - sum(d for i, d in enumerate(deg) if i != p["ai"])
    return F(p["N"] * (deg[p["ai"]] - deg[p["bi"]]), 360)


@template(T, "competent", MIX)
def pie_work_back(r):
    """math-pat-pie-chart-reading. Work back from the count in one labelled sector to the total, then find the unlabelled sector."""
    c = r.choice(CAT)
    n = r.choice([4, 5])
    labs, parts = pie_sectors(r, c, n)
    ai, yi = r.sample(range(n), 2)
    N = r.choice([100, 120, 160, 200, 240, 300, 400, 500])
    M = N * parts[yi] // 100
    use_f = all(p in FRAC_OK for p in parts) and r.random() < 0.5
    shows = [None if i == ai else plab(p, use_f) for i, p in enumerate(parts)]
    others = sum(p for i, p in enumerate(parts) if i != ai)
    ans = N * parts[ai] // 100
    kind = c["one"].format(a=labs[ai])
    unit = c["noun"]
    stem = (f"The pie chart shows how some {unit} were counted by type. There were {M} {unit} of type {labs[yi]}. "
            f"{kind}")
    wrong = [(M * parts[ai] // 100, "treated_count_as_total", f"Treated {M} as the whole instead of as the {labs[yi]} sector."),
             (N, "gave_the_total", "Stopped at the total."),
             (M * (100 - others) // 100 + M, "added_given_count", "Added the given count to a wrong share."),
             (parts[ai], "percent_as_amount", "Gave the percentage as the amount.")]
    return build(pie_work_back, stem, ans, wrong,
                 [f"{labs[yi]} is {parts[yi]}% = {M}, so 1% = {M / parts[yi]:g}.", f"Total = {N}.",
                  f"{labs[ai]} = 100% - {others}% = {parts[ai]}%; {parts[ai]}% of {N} = {ans}"],
                 {"parts": parts, "ai": ai, "yi": yi, "M": M}, whole=True, figure=pie_fig(labs, parts, shows, c["title"]))


@checker(pie_work_back)
def _(p):
    # ratio route: amounts are in the ratio of the sector sizes
    rest = 100 - sum(x for i, x in enumerate(p["parts"]) if i != p["ai"])
    return F(p["M"] * rest, p["parts"][p["yi"]])


@template(T, "competent", MIX)
def line_greatest_increase(r):
    """Largest increase between consecutive readings of a line graph."""
    c = r.choice([l for l in LINE if l["title"] != "Savings ($)"] + [LINE[1]])
    step = r.choice(c["steps"])
    while True:
        ks = line_ks(r, c, "wiggle")
        inc = [ks[i + 1] - ks[i] for i in range(len(ks) - 1)]
        top = sorted(inc)[-1]
        if top > 0 and inc.count(top) == 1 and min(inc) < 0:
            break
    vals = [k * step for k in ks]
    ans = top * step
    drop = -min(inc) * step
    second = sorted(inc)[-2] * step
    stem = f"{lead(r, 'line graph', c['intro'])} What was the greatest increase in {c['meas']} between two consecutive readings?"
    wrong = [(drop, "greatest_drop_instead", "Found the greatest drop instead of the greatest increase."),
             ((vals[-1] - vals[0] if vals[-1] > vals[0] else None), "first_to_last", "Found the change from the first to the last reading."),
             (second if second > 0 else None, "second_greatest", "Gave the second largest increase."),
             (max(vals), "gave_highest_reading", "Gave the highest reading, not an increase."),
             (ans + step, "miscounted_units", "Miscounted by one gridline.")]
    return build(line_greatest_increase, stem, ans, wrong,
                 ["Work out each change from one reading to the next.", f"The greatest rise is {ans}."],
                 {"vals": vals}, show=lfmt(c), whole=True,
                 figure=line_graph([c["xlab"](x) for x in c["xs"]], vals, c["title"], step=step))


@checker(line_greatest_increase)
def _(p):
    v = p["vals"]
    return F(max(b - a for a, b in zip(v, v[1:])))


@template(T, "competent", MIX)
def line_extend(r):
    """math-pat-line-graph-rate-and-time"""
    c = r.choice([x for x in RATE if x["up"]])
    while True:
        ks, ds = rate_series(r, True)
        if ds[2] > 0:
            break
    step = r.choice([10, 20, 25])
    vals = [k * step for k in ks]
    R = ds[2] * step // 5
    m = r.randint(2, 12)
    V = vals[-1] + R * m
    stem = (f"{lead(r, 'line graph', c['intro'])} After 30 minutes, {c['flow']} at the same rate as between 20 and 30 minutes. "
            f"After how many more minutes will the volume reach {V} litres?")
    need = V - vals[-1]
    wrong = [(need, "forgot_to_divide_by_rate", "Gave the extra litres needed, not the time."),
             (V // R if V % R == 0 else None, "measured_from_zero", "Divided the target volume by the rate, as if starting from empty."),
             (m + 1, "slip_in_division", "Slip in the division."),
             (max(m - 1, 1), "slip_in_division", "Slip in the division."),
             (F(need, ds[2] * step), "used_change_per_interval", "Divided by the change over 5 minutes instead of the rate per minute.")]
    return build(line_extend, stem, m, wrong,
                 [f"Rate = {vals[-1] - vals[-3]} L / 10 min = {R} L per minute.", f"Still needed: {V} - {vals[-1]} = {need} L.",
                  f"Time = {need} / {R} = {m} minutes"],
                 {"v1": vals[-3], "v2": vals[-1], "V": V}, whole=True,
                 figure=line_graph([str(x) for x in MINS], vals, c["title"], step=step))


@checker(line_extend)
def _(p):
    rate = F(p["v2"] - p["v1"], 10)
    v, t = F(p["v2"]), 0
    while v < p["V"]:
        v += rate
        t += 1
    return F(t)


@template(T, "competent", BAR, MIX)
def bar_percent(r):
    """math-pat-table-bar-graph-reading"""
    c = r.choice(CAT)
    n = r.choice([4, 5])
    labs = r.sample(c["cats"], n)
    while True:
        step = r.choice([5, 10, 20, 25])
        Tt = r.choice([50, 100, 200])
        if Tt % step:
            continue
        ks = [r.randint(1, 8) for _ in range(n)]
        if sum(ks) * step == Tt and len(set(ks)) == n and (Tt != 200 or all((k * step) % 2 == 0 for k in ks)):
            break
    vals = [k * step for k in ks]
    i = r.randrange(n)
    ans = vals[i] * 100 // Tt
    stem = f"{lead(r, 'bar graph', c['intro'])} {c['pctq'].format(a=labs[i])}"
    mx = max(vals)
    wrong = [(vals[i], "gave_value_as_percent", "Gave the bar value as the percentage.") if Tt != 100 else (None, "", ""),
             (F(vals[i] * 100, mx), "compared_with_largest", "Compared the bar with the largest bar instead of the total."),
             (F(vals[i] * 100, Tt - vals[i]), "compared_with_the_rest", "Divided by the other bars instead of the total."),
             (ans + 5, "slip_in_percentage", "Slip when converting to a percentage."),
             (max(ans - 5, 5), "slip_in_percentage", "Slip when converting to a percentage.")]
    return build(bar_percent, stem, ans, wrong,
                 [f"Total = {Tt}.", f"{vals[i]} / {Tt} x 100 = {ans}%"], {"vals": vals, "i": i}, show=pct, whole=True,
                 unit_size=None, figure=bar_chart(labs, vals, c["title"], c["yl"], step=step), auto_slips=False)


@checker(bar_percent)
def _(p):
    v = p["vals"]
    return F(sum(1 for _ in range(1)) * v[p["i"]] * 100, sum(v))


@template(T, "competent", TABLE, MIX)
def table_missing_cell(r):
    """Find a missing number in a table from the totals."""
    c = r.choice([TAB[0], TAB[2]])
    rows = r.sample(NAMES, 3) if c["rows"] == "NAMES" else list(c["rows"])[:3]
    cols = c["cols"][:2]
    g = [[r.randint(10, 60), r.randint(10, 60)] for _ in range(3)]
    rt = [sum(x) for x in g]
    ct = [sum(g[i][j] for i in range(3)) for j in range(2)]
    G = sum(rt)
    ra, ca = r.randrange(3), r.randrange(2)
    oc = 1 - ca
    hdr = [""] + cols + ["Total"]
    body = []
    for i in range(3):
        row = [rows[i], str(g[i][0]), str(g[i][1]), "-" if i == ra else str(rt[i])]
        body.append(row)
    body.append(["Total", str(ct[0]), str(ct[1]), str(G)])
    body[3][ca + 1] = "-"
    body[ra][ca + 1] = "?"
    fig = table_fig(hdr, body, title=c["title"], blanks={(ra, ca + 1)})
    ans = g[ra][ca]
    ocol = ct[oc]
    others = sum(g[i][ca] for i in range(3) if i != ra)
    wrong = [(G - ocol, "forgot_known_cells", "Found the column total but did not subtract the known cells."),
             (G - ocol + others, "added_known_cells", "Added the known cells instead of subtracting them."),
             (rt[(ra + 1) % 3] - g[(ra + 1) % 3][ca], "used_wrong_row", "Worked out a cell in a different row."),
             (G - sum(rt[i] for i in range(3) if i != ra), "found_row_total_only", "Found the row total, not the cell.")]
    stem = (f"{lead(r, 'table', c['intro'])} A dash means the number is not given. "
            f"Find the number in the cell marked ?. The totals in the last row and column are correct.")
    return build(table_missing_cell, stem, ans, wrong,
                 [f"Column total of the other column: {ocol}.", f"Column total for this column = {G} - {ocol} = {G - ocol}.",
                  f"Subtract the known cells: {G - ocol} - {others} = {ans}"],
                 {"g": g, "ra": ra, "ca": ca, "G": G, "rt": rt}, whole=True, figure=fig)


@checker(table_missing_cell)
def _(p):
    # other route: row total of the unknown row, then subtract the other cell in that row
    g, ra, ca = p["g"], p["ra"], p["ca"]
    row_total = p["G"] - sum(p["rt"][i] for i in range(3) if i != ra)
    return F(row_total - g[ra][1 - ca])


@template(T, "competent", PIC2, MIX)
def picture_money(r):
    """math-pat-table-bar-graph-reading"""
    c = r.choice(SELL_CAT)
    n = r.randint(4, 5)
    labs = r.sample(c["cats"], n)
    key = r.choice([2, 4, 5, 10])
    halves = r.sample(range(2, 15), n)
    counts = [h * key // 2 for h in halves]
    price = r.choice(c["sell"][1])
    i, j = r.sample(range(n), 2)
    ans = (counts[i] + counts[j]) * price
    stem = (f"{lead(r, 'picture graph', c['intro'])} {c['sell'][0].format(p=price)} "
            f"How much money was collected from {labs[i]} and {labs[j]} altogether?")
    sy = (halves[i] + halves[j]) / 2
    wrong = [(counts[i] + counts[j], "forgot_price", "Found the number sold but not the money."),
             (sy * price, "ignored_key", "Counted symbols instead of items when finding the money."),
             (counts[i] * price, "used_one_category", "Found the money for one category only."),
             (abs(counts[i] - counts[j]) * price, "subtracted_instead_of_adding", "Subtracted instead of adding.")]
    return build(picture_money, stem, ans, wrong,
                 [f"Each symbol is {key}.", f"Items sold: {counts[i]} + {counts[j]} = {counts[i] + counts[j]}.",
                  f"Money = {counts[i] + counts[j]} x ${price} = ${ans}"],
                 {"counts": counts, "i": i, "j": j, "price": price}, show=money, whole=True,
                 figure=picture_graph(labs, counts, key, c["noun"], c["title"]))


@checker(picture_money)
def _(p):
    return F(p["counts"][p["i"]] * p["price"] + p["counts"][p["j"]] * p["price"])


@template(T, "competent", BAR, MIX)
def bar_profit(r):
    """Money and cost from a bar graph."""
    c = r.choice(SELL_TIME)
    n = r.randint(5, 6)
    labs = c["cats"][:n]
    step, vals = step_vals(r, n, steps=(10, 20, 25, 50), kmin=2, kmax=8)
    price = r.choice(c["sell"][1])
    i, j = r.sample(range(n), 2)
    cost = r.choice([20, 30, 40, 50, 60])
    ans = (vals[i] + vals[j]) * price - 2 * cost
    if ans <= 0:
        return None
    stem = (f"{lead(r, 'bar graph', c['intro'])} {c['sell'][0].format(p=price)} The expenses are "
            f"${cost} each {c['per']}. What was the total profit for {labs[i]} and {labs[j]}?")
    rev = (vals[i] + vals[j]) * price
    wrong = [(rev - cost, "cost_counted_once", f"Took away the cost for one {c['per']} only."),
             (rev, "ignored_cost", "Gave the money collected and did not take away the cost."),
             (vals[i] + vals[j] - 2 * cost, "forgot_price", "Subtracted the cost from the number sold instead of the money."),
             ((vals[i] + vals[j]) * price - cost * price * 2, "multiplied_cost_by_price", "Multiplied the cost by the price.")]
    return build(bar_profit, stem, ans, wrong,
                 [f"Number sold: {vals[i]} + {vals[j]} = {vals[i] + vals[j]}.", f"Money = {vals[i] + vals[j]} x ${price} = ${rev}.",
                  f"Cost = 2 x ${cost} = ${2 * cost}.", f"Profit = ${rev} - ${2 * cost} = ${ans}"],
                 {"va": vals[i], "vb": vals[j], "price": price, "cost": cost}, show=money, whole=True,
                 figure=bar_chart(labs, vals, c["title"], c["yl"], step=step))


@checker(bar_profit)
def _(p):
    return F(sum(p["price"] - 0 for _ in range(p["va"])) + sum(p["price"] for _ in range(p["vb"])) - p["cost"] - p["cost"])


@template(T, "competent", BAR, MIX)
def bar_new_average(r):
    """math-pat-graph-find-missing-from-average"""
    c = r.choice(TIME)
    labs = c["cats"][:5]
    while True:
        step, vals = step_vals(r, 6, steps=(2, 4, 5, 10, 20), kmin=2, kmax=9)
        if sum(vals) % 6 == 0:
            break
    first, nxt = vals[:5], vals[5]
    avg = sum(vals) // 6
    old = sum(first)
    stem = (f"{lead(r, 'bar graph', c['intro'])} The graph shows the first 5 {c['per']}s. "
            f"After the next {c['per']}, the average for all 6 {c['per']}s was {avg}. What was the value for the next {c['per']}?")
    wrong = [(6 * avg, "gave_the_total", "Found the total for 6 and did not subtract the first 5."),
             (5 * avg - old, "used_wrong_count", "Used 5 instead of 6 for the number of values."),
             (avg, "gave_the_average", "Assumed the new value equals the new average."),
             (F(old, 5), "old_average", "Found the average of the first 5 only.")]
    return build(bar_new_average, stem, nxt, wrong,
                 [f"Total for 6 = {avg} x 6 = {6 * avg}.", f"First 5 add to {old}.", f"{6 * avg} - {old} = {nxt}"],
                 {"old": old, "avg": avg}, whole=True, unit_size=step,
                 figure=bar_chart(labs, first, c["title"], c["yl"], step=step))


@checker(bar_new_average)
def _(p):
    return F(next(x for x in range(1, 100000) if (p["old"] + x) == 6 * p["avg"]))


PCT_PAIRS = [(2, 3), (2, 4), (4, 5), (4, 6), (5, 6), (5, 7), (4, 7), (2, 5), (1, 2), (3, 4), (5, 8), (1, 3)]
PCT_OK = [(a, b) for a, b in PCT_PAIRS if (100 * (b - a)) % a == 0]


@template(T, "competent", MIX)
def line_pct_increase(r):
    """Percentage increase between two readings of a line graph."""
    c = r.choice([LINE[0], LINE[1], LINE[3]])  # not temperature: a % change of a deg C reading is meaningless
    step = r.choice(c["steps"])
    n = len(c["xs"])
    a, b = r.choice(PCT_OK)
    i, j = sorted(r.sample(range(n), 2))
    ks = [r.randint(1, 8) for _ in range(n)]
    ks[i], ks[j] = a, b
    vals = [k * step for k in ks]
    ans = (b - a) * 100 // a
    stem = (f"{lead(r, 'line graph', c['intro'])} Find the percentage increase in {c['meas']} from "
            f"{c['at'](c['xs'][i])} to {c['at'](c['xs'][j])}.")
    wrong = [(F((b - a) * 100, b), "divided_by_new_value", "Divided the increase by the new value instead of the old value."),
             (b * 100 // a if (b * 100) % a == 0 else None, "gave_new_as_percent_of_old", "Gave the new value as a percentage of the old value."),
             ((b - a) * step, "gave_the_increase", "Gave the increase in value, not a percentage."),
             (ans + 5, "slip_in_percentage", "Slip in the percentage."),
             (max(ans - 10, 5), "slip_in_percentage", "Slip in the percentage.")]
    return build(line_pct_increase, stem, ans, wrong,
                 [f"Old = {a * step}, new = {b * step}.", f"Increase = {(b - a) * step}.",
                  f"{(b - a) * step} / {a * step} x 100 = {ans}%"],
                 {"old": a * step, "new": b * step}, show=pct, whole=True, auto_slips=False,
                 figure=line_graph([c["xlab"](x) for x in c["xs"]], vals, c["title"], step=step))


@checker(line_pct_increase)
def _(p):
    return F(next(q for q in range(1, 1000) if p["old"] * (100 + q) == p["new"] * 100))
