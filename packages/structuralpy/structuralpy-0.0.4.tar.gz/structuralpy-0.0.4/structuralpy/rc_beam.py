# structuralpy/rc_beam.py
import math
import sympy as sp

def beta_1(fcp) :
    if fcp <= 28 :
        return 0.85
    elif fcp > 56 :
        return 0.65
    else :
        return 0.85 - 0.05/7*(fcp - 28)

def analyze_flexure(b, h, fcp, fy, As, cover_bot, Asp=0, cover_top=None, n_iter=10) :
    """
    Calculate the ultimate moment capacity of a rectangular RC beam in flexure.

    Parameters:

    - `b` (float)      : Beam width in mm.
    - `h` (float)      : Beam depth in mm.
    - `fcp` (float)    : Concrete 28-day compressive strength in MPa.
    - `fy` (float)     : Reinforcement yield strength in MPa.
    - `As` (float)     : Tension main reinforcement area in mm^2.
    - `cover_bot` (mm) : Cover to centroid of tension reinforcement in mm.
    - `Asp` (float)    : Compression main reinforcement area in mm^2. Default value is 0 (no reinforcement).
    - `cover_top` (mm) : Cover to centroid of compression reinforcement in mm. Default value is None (same as cover_bot).
    - `n_iter` (int)   : Number of iterations for iterative solving of equilibrium equation. Default value is 10.

    Returns:
    
    - (float) : The ultimate moment capacity in flexure in N-mm.
    """
    # Effective depths
    if cover_top is None :
        cover_top = cover_bot
    d = h - cover_bot
    dp = cover_top

    # First assume both top and bottom reinforcements yield.
    fs = fy
    fsp = fy
    for _ in range(n_iter) :
        # Locate the neutral axis.
        c = (As*fs - Asp*(fsp - 0.85*fcp))/(0.85*fcp*beta_1(fcp)*b)
        # Update the stresses in both reinforcements.
        fs = min(600*(d - c)/c, fy)
        fsp = min(600*(c - dp)/c, fy)

    # Strength reduction factor
    fs_ = 600*(d - c)/c
    if fs_ >= 1000 :
        phi = 0.90
    elif fs_ < fy :
        phi = 0.65
    else :
        phi = 0.65 + 0.25*(fs_ - fy)/(1000 - fy)

    # Depth of compression block
    a = beta_1(fcp)*c
    Ac = a*b - Asp if a >= dp else a*b
    # Nominal moment capacity.
    Mn = 0.85*fcp*Ac*(d - a/2) + Asp*fsp*(d - dp)

    return phi*Mn

def design_flexure_size(Mu, fcp, fy, cover_bot, aspect_ratio=2.0) :
    """
    Calculate the smallest economical size of the beam in flexure.

    Parameters:

    - `Mu` (float)           : Factored moment in mm.
    - `fcp` (float)          : Concrete 28-day compressive strength in MPa.
    - `fy` (float)           : Tension reinforcement yield strength in MPa.
    - `cover_bot` (float)    : Cover to centroid of tension reinforcement in mm.
    - `aspect_ratio` (float) : Depth to width ratio of the beam. Default value is 2.

    Returns:
    
    - (int, int) : Beam width and depth rounded to the nearest higher 50 mm.
    """
    b_sym = sp.Symbol("b")

    phi = 0.90
    beta1 = max(min(0.85 - 0.05/7*(fcp - 28), 0.85), 0.65)
    rho5 = 3/8 * 0.85*fcp*beta1/fy
    omega5 = rho5*fy/fcp
    eqn = sp.Eq(Mu, phi*b_sym*(aspect_ratio*b_sym - cover_bot)**2*fcp*omega5*(1 - 10*omega5/17))
    b = sp.solve(eqn, b_sym)[0]
    d = aspect_ratio*b
    h = d + cover_bot

    b = max(math.ceil(b/50)*50, 200)
    h = max(math.ceil(h/50)*50, 200)
    
    return (b, h)

def design_flexure_rebar(Mu, b, h, fcp, fy, cover_bot, cover_top=None) :
    """
    Calculate the tension or compression reinforcement of the beam in flexure.

    Parameters:

    - `Mu` (float)           : Factored moment in mm. If Mu >= 0, then tension reinforcement; if Mu < 0, then compression reinforcement.
    - `b` (float)            : Beam width in mm.
    - `h` (float)            : Beam depth in mm.
    - `fcp` (float)          : Concrete 28-day compressive strength in MPa.
    - `fy` (float)           : Tension reinforcement yield strength in MPa.
    - `cover_bot` (float)    : Cover to centroid of tension reinforcement in mm.
    - `cover_top` (mm)       : Cover to centroid of compression reinforcement in mm. Default value is None (same as cover_bot).

    Returns:
    
    - (float, float)         : Total area of bottom and top reinforcment, both in mm^2.
    """
    if cover_top is None :
        cover_top = cover_bot

    phi = 0.90
    d = h - cover_bot
    dp = h - cover_top
    m = fy/(0.85*fcp)
    rho_min = max(1.4, 0.25*math.sqrt(fcp))/fy

    Mu_ = Mu if Mu >= 0 else abs(Mu)
    Rn = Mu_/(phi*b*(d if Mu >= 0 else dp)**2)
    rho = 1/m*(1 - math.sqrt(1 - 2*m*Rn/fy))
    rho = max(rho, rho_min)
    As = rho*b*(d if Mu >= 0 else dp)

    return (As, 0) if Mu >= 0 else (0, As)