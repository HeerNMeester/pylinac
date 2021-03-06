"""
The TG-51 module contains a number of helper functions and classes that can calculate parameters for performing the
TG-51 absolute linac dose calibration. Functions include all relevant calculations for TG-51 including PDDx, kQ,
Dref, and chamber reading corrections.

Classes include photon and electron calibrations using cylindrical chambers. Pass all the relevant raw measurements
and the class will compute the corrected values and dose at 10cm and dmax/dref.
"""
import numpy as np

from pylinac.core.utilities import Structure


CHAMBERS = {
    # Exradin
    'A12': {"a": 1.0146, "b": 0.777e-3, "c": -1.666e-5, "a'": 2.6402, "b'": -7.2304, "c'": 10.7573, "d'": -5.4294, 'kecal': 0.906},
    'A19': {"a": 0.9934, "b": 1.384e-3, "c": -2.125e-5, "a'": 3.0907, "b'": -9.1930, "c'": 13.5957, "d'": -6.7969},
    'A2': {"a": 0.9819, "b": 1.609e-3, "c": -2.184e-5, "a'": 2.8458, "b'": -8.1619, "c'": 12.1411, "d'": -6.1041},
    'T2': {"a": 1.0173, "b": 0.854e-3, "c": -1.941e-5, "a'": 3.3433, "b'": -10.2649, "c'": 15.1247, "d'": -7.5415},
    'A12S': {"a": 0.9692, "b": 1.974e-3, "c": -2.448e-5, "a'": 2.9597, "b'": -8.6777, "c'": 12.9155, "d'": -6.4903},
    'A18': {"a": 0.9944, "b": 1.286e-3, "c": -1.980e-5, "a'": 2.5167, "b'": -6.7567, "c'": 10.1519, "d'": -5.1709},
    'A1': {"a": 1.0029, "b": 1.023e-3, "c": -1.803e-5, "a'": 2.0848, "b'": -4.9174, "c'": 7.5446, "d'": -3.9441, 'kecal': 0.915},
    'T1': {"a": 1.0552, "b": -0.196e-3, "c": -1.275e-5, "a'": 2.8060, "b'": -7.9273, "c'": 11.7541, "d'": -5.9263},
    'A1SL': {"a": 0.9896, "b": 1.410e-3, "c": -2.049e-5, "a'": 2.8029, "b'": -7.9648, "c'": 11.8445, "d'": -5.9568},
    'A14': {"a": 0.9285, "b": 2.706e-3, "c": -2.599e-5, "a'": 5.4677, "b'": -19.1795, "c'": 27.4542, "d'": -13.1336},
    'T14': {"a": 0.9622, "b": 2.009e-3, "c": -2.401e-5, "a'": 4.9690, "b'": -17.1074, "c'": 24.6292, "d'": -11.8877},
    'A14SL': {"a": 0.9017, "b": 3.454e-3, "c": -3.083e-5, "a'": 5.1205, "b'": -17.7884, "c'": 25.6123, "d'": -12.3232},
    'A16': {"a": 0.8367, "b": 4.987e-3, "c": -3.877e-5, "a'": 6.0571, "b'": -21.7829, "c'": 31.2289, "d'": -14.9168},

    # PTW
    '30010': {"a": 1.0093, "b": 0.926e-3, "c": -1.771e-5, "a'": 2.5318, "b'": -6.7948, "c'": 10.1779, "d'": -5.1746},
    '30011': {"a": 0.9676, "b": 2.061e-3, "c": -2.528e-5, "a'": 2.9044, "b'": -8.4576, "c'": 12.6339, "d'": -6.3742},
    '30012': {"a": 0.9537, "b": 2.440e-3, "c": -2.750e-5, "a'": 3.2836, "b'": -10.0610, "c'": 14.8867, "d'": -7.4212},
    '30013': {"a": 0.9652, "b": 2.141e-3, "c": -2.623e-5, "a'": 3.2012, "b'": -9.7211, "c'": 14.4211, "d'": -7.2184},
    '31010': {"a": 0.9590, "b": 2.265e-3, "c": -2.684e-5, "a'": 3.1578, "b'": -9.5422, "c'": 14.1676, "d'": -7.0964},
    '31016': {"a": 1.0085, "b": 1.028e-3, "c": -1.968e-5, "a'": 2.9524, "b'": -8.6054, "c'": 12.7757, "d'": -6.4265},
    '31014': {"a": 1.0071, "b": 1.048e-3, "c": -1.967e-5, "a'": 3.0178, "b'": -8.8735, "c'": 13.1372, "d'": -6.5867},

    # IBA
    'CC25': {"a": 0.9551, "b": 2.353e-3, "c": -2.687e-5, "a'": 2.4567, "b'": -6.5932, "c'": 10.0471, "d'": -5.1775},
    'CC13': {"a": 0.9515, "b": 2.455e-3, "c": -2.768e-5, "a'": 3.1982, "b'": -9.7182, "c'": 14.4210, "d'": -7.2121},
    'CC08': {"a": 0.9430, "b": 2.637e-3, "c": -2.884e-5, "a'": 3.7328, "b'": -11.9800, "c'": 17.5884, "d'": -8.6843},
    'CC04': {"a": 0.9714, "b": 1.938e-3, "c": -2.432e-5, "a'": 3.0054, "b'": -8.8633, "c'": 13.1704, "d'": -6.6075},
    'CC01': {"a": 0.9116, "b": 3.358e-3, "c": -3.177e-5, "a'": 4.3376, "b'": -14.4935, "c'": 21.0293, "d'": -10.2208},
    'FC65-G': {"a": 0.9708, "b": 1.972e-3, "c": -2.480e-5, "a'": 3.3221, "b'": -10.2012, "c'": 15.0497, "d'": -7.4872},
    'FC65-P': {"a": 0.9828, "b": 1.664e-3, "c": -2.296e-5, "a'": 3.0872, "b'": -9.1919, "c'": 13.6137, "d'": -6.8118},
    'FC23-C': {"a": 0.9820, "b": 1.579e-3, "c": -2.166e-5, "a'": 3.0511, "b'": -9.0243, "c'": 13.3378, "d'": -6.6559},

    # Other
    'NE2581': {"a": 1.0318, "b": 0.488e-3, "c": -1.731e-5, "a'": 2.9190, "b'": -8.4561, "c'": 12.5690, "d'": -6.3468, 'kecal': 0.885},
    'NE2571': {"a": 0.9882, "b": 1.486e-3, "c": -2.140e-5, "a'": 2.2328, "b'": -5.5779, "c'": 8.5325, "d'": -4.4352, 'kecal': 0.903},
    'NE2561': {"a": 1.0200, "b": 0.596e-3, "c": -1.551e-5, "a'": 2.4235, "b'": -6.3179, "c'": 9.4737, "d'": -4.8307, 'kecal': 0.904},
    'PR06C/G': {"a": 0.9519, "b": 2.432e-3, "c": -2.704e-5, "a'": 2.9110, "b'": -8.4916, "c'": 12.6817, "d'": -6.3874, 'kecal': 0.900},
}


def p_tp(temp=22, press=760):
    """Calculate the temperature & pressure correction.

    Parameters
    ----------
    temp : float
        The temperature in degrees Celsius.
    press : float
        The pressure in mmHg.
    """
    return (760/press)*((273.2+temp)/295.2)


def p_pol(m_reference=(1, 2), m_opposite=(-3, -4)):
    """Calculate the polarity correction.

    Parameters
    ----------
    m_reference : iterable
        The readings of the ion chamber at the reference polarity and voltage.
    m_opposite : iterable
        The readings of the ion chamber at the polarity opposite the reference.
        This value should be of the opposite sign of the M reference value.
        If it's not, its sign will automatically be flipped.
    """
    mref_avg = np.mean(m_reference)
    mopp_avg = np.mean(m_opposite)
    # if same sign given, flip one.
    # Technically, they're opposite charges, but most physicists pass positive values for both
    if np.sign(mref_avg) == np.sign(mopp_avg):
        mopp_avg = -mopp_avg
    return (mref_avg - mopp_avg)/(2*mref_avg)


def p_ion(volt_high=300, volt_low=150, m_high=(1, 2), m_low=(3, 4)):
    """Calculate the ion chamber collection correction.

    Parameters
    ----------
    volt_high : int
        The "high" voltage; same as the TG51 measurement voltage.
    volt_low : int
        The "low" voltage; usually half of the high voltage.
    m_high : iterable
        The readings of the ion chamber at the "high" voltage.
    m_low : iterable
        The readings of the ion chamber at the "low" voltage.
    """
    return (1 - volt_high/volt_low)/(np.mean(m_high)/np.mean(m_low) - volt_high/volt_low)


def d_ref(i_50):
    """Calculate the dref of an electron beam based on the I50 depth.

    Parameters
    ----------
    i_50 : float
        The value of I50 in cm.
    """
    r50 = r_50(i_50)
    return 0.6*r50-0.1


def r_50(i_50):
    """Calculate the R50 depth of an electron beam based on the I50 depth.

    Parameters
    ----------
    i_50 : float
        The value of I50 in cm.
    """
    if i_50 < 10:
        r50 = 1.029 * i_50 - 0.06
    else:
        r50 = 1.59 * i_50 - 0.37
    return r50


def kp_r50(r_50):
    """Calculate k'R50 for Farmer-like chambers.

    Parameters
    ----------
    r_50 : float
        The R50 value in cm.
    """
    if r_50 >= 9 or r_50 <= 2:
        raise ValueError("Cannot calculate k prime R50 with an R50 value of <=2 or >=9cm")
    return 0.9905+0.071*np.exp(-r_50/3.67)


def pq_gr(m_dref_plus=(1, 2), m_dref=(3, 4)):
    """Calculate PQ_gradient for a cylindrical chamber.

    Parameters
    ----------
    m_dref_plus : iterable
        The readings of the ion chamber at dref + 0.5rcav.
    m_dref : iterable
        The readings of the ion chamber at dref.
    """
    return np.mean(m_dref_plus) / np.mean(m_dref)


def m_corrected(p_ion=1.0, p_tp=1.0, p_elec=1.0, p_pol=1.0, m_raw=(1.1, 2.2)):
    """Calculate M_corrected, the ion chamber reading with all corrections applied.

    Parameters
    ----------
    p_ion : float
        The ion collection correction.
    p_tp : float
        The temperature & pressure correction.
    p_elec : float
        The electrometer correction.
    p_pol : float
        The polarity correction.
    m_raw : iterable
        The raw ion chamber readings.

    Returns
    -------
    float
    """
    return p_ion*p_tp*p_elec*p_pol*np.mean(m_raw)


def pddx(pdd=66.4, energy=6, lead_foil=None):
    """Calculate PDDx based on the PDD.

    Parameters
    ----------
    pdd : {>0.627, <0.890}
        The measured PDD. If lead foil was used, this assumes the pdd as measured with the lead in place.
    energy : int
        The nominal energy in MV.
    lead_foil : {None, '30cm', '50cm'}
        Applicable only for energies >10MV.
        Whether a lead foil was used to acquire the pdd.
        Use ``None`` if no lead foil was used and the interim equation should be used.
        Use ``50cm`` if the lead foil was set to 50cm from the phantom surface.
        Use ``30cm`` if the lead foil was set to 30cm from the phantom surface.
    """
    if energy < 10:
        return pdd
    elif energy >= 10:
        if lead_foil is None:
            return 1.267*pdd-20
        elif lead_foil == '50cm':
            if pdd < 73:
                return pdd
            else:
                return (0.8905+0.0015*pdd)*pdd
        elif lead_foil == '30cm':
            if pdd < 71:
                return pdd
            else:
                return (0.8116+0.00264*pdd)*pdd


def kq(model='30010', pddx=None, tpr=None):
    """Calculate kq based on the model and clinical measurements.

    Parameters
    ----------
    model : str
        The model of the chamber. Valid values are those listed in
        Table III of Muir and Rodgers and Table I of the TG-51 Addendum.
    pddx : {>=0.627, <=0.861}
        The PHOTON-ONLY PDD measurement at 10cm depth for a 10x10cm2 field.
    tpr : {>=0.623, <=0.805}
        The TPR ratio of the 20cm measurement divided by the 10cm measurement.


    .. warning::
        Only ``pddx`` or ``tpr`` can be defined, not both.
    """
    PDD_LOW = 62.7
    PDD_HIGH = 86.1
    TPR_LOW = 0.623
    TPR_HIGH = 0.805

    if pddx is not None and tpr is not None:
        raise ValueError("Only the PDD or TPR parameter can be defined, not both.")
    if pddx is None and tpr is None:
        raise ValueError("Either the TPR or PDD must be defined.")

    if pddx is not None:
        if pddx > PDD_HIGH or pddx < PDD_LOW:
            raise ValueError("Measured PDD is out of range; must be between {:2.2} and {:2.2}.".format(PDD_LOW, PDD_HIGH))
        else:
            ch = CHAMBERS[model]
            return ch["a"] + ch["b"]*pddx + ch["c"]*(pddx**2)

    if tpr is not None:
        if tpr > TPR_HIGH or tpr < TPR_LOW:
            raise ValueError("Measured TPR is out of range; must be between {:2.2} and {:2.2}.".format(TPR_LOW, TPR_HIGH))
        else:
            ch = CHAMBERS[model]
            return ch["a'"] + ch["b'"]*tpr + ch["c'"]*(tpr**2) + ch["d'"]*(tpr**3)


class TG51Base(Structure):

    @property
    def p_tp(self):
        """Temperature/Pressure correction."""
        return p_tp(self.temp, self.press)

    @property
    def p_ion(self):
        """Ionization collection correction."""
        return p_ion(self.volt_high, self.volt_low, self.m_raw, self.m_low)

    @property
    def p_pol(self):
        """Polarity correction."""
        return p_pol(self.m_raw, self.m_opp)

    @property
    def m_corrected(self):
        """Corrected chamber reading."""
        return m_corrected(self.p_ion, self.p_tp, self.p_elec, self.p_pol, self.m_raw)


class TG51Photon(TG51Base):
    """Class for calculating absolute dose to water using a cylindrical chamber in a photon beam.

    Attributes
    ----------
    temp : float
    press : float
    energy : float
        Nominal energy of the beam in MV.
    model : str
        Chamber model
    n_dw : float
        NDW value in Gy/nC
    p_elec : float
    measured_pdd : float
        The measured value of PDD(10); used for calculating kq.
    lead_foil : {None, '50cm', '30cm'}
        Whether a lead foil was used to acquire PDD(10)x and where its position was. Used to calculate kq.
    clinical_pdd : float
        The PDD used to correct the dose at 10cm back to dmax. Usually the TPS PDD(10) value.
    volt_high : float
    volt_low : float
    m_raw : float, tuple
    m_opp : float, tuple
    m_low : float, tuple
    mu : float
    tissue_correction : float
        Correction value to calibration to, e.g., muscle. A value of 1.0 means no correction (i.e. water).
    """

    def __init__(self, temp=22,
                 press=760,
                 model='30010',
                 n_dw=5.9,
                 p_elec=1.0,
                 measured_pdd=66.4,
                 lead_foil=None,
                 clinical_pdd=66.4,
                 energy=6,
                 volt_high=300,
                 volt_low=150,
                 m_raw=(1, 2),
                 m_opp=(1, 2),
                 m_low=(1, 2),
                 mu=200,
                 tissue_correction=1.0):
        super().__init__(temp=temp, press=press, model=model, n_dw=n_dw, p_elec=p_elec, measured_pdd=measured_pdd,
                         energy=energy, volt_high=volt_high, volt_low=volt_low, m_raw=m_raw,
                         m_opp=m_opp, m_low=m_low, clinical_pdd=clinical_pdd, mu=mu,
                         tissue_correction=tissue_correction, lead_foil=lead_foil)

    @property
    def pddx(self):
        """The photon-only PDD(10) value."""
        return pddx(self.measured_pdd, self.energy, self.lead_foil)

    @property
    def kq(self):
        """The chamber-specific beam quality correction factor."""
        return kq(self.model, self.pddx)

    @property
    def dose_mu_10(self):
        """cGy/MU at a depth of 10cm."""
        return self.tissue_correction * self.m_corrected * self.kq * self.n_dw / self.mu

    @property
    def dose_mu_dmax(self):
        """cGy/MU at a depth of dmax."""
        return self.dose_mu_10 / (self.clinical_pdd / 100)


class TG51Electron(TG51Base):
    """Class for calculating absolute dose to water using a cylindrical chamber in an electron beam.

    Attributes
    ----------
    temp : float
    press : float
    model : str
        Chamber model
    n_dw : float
        NDW value in Gy/nC
    p_elec : float
    clinical_pdd : float
        The PDD used to correct the dose at 10cm back to dmax. Usually the TPS PDD(10) value.
    volt_high : float
    volt_low : float
    m_raw : float, tuple
    m_opp : float, tuple
    m_low : float, tuple
    mu : float
    i_50 : float
        Depth of 50% ionization
    k_ecal : float
    m_plus : float, tuple
        The measurement at 0.5rcav+dref to calculate P gradient
    tissue_correction : float
        Correction value to calibration to, e.g., muscle. A value of 1.0 means no correction (i.e. water).
    """

    def __init__(self, temp=22, press=760, model='30010', n_dw=5.9, p_elec=1.0,
                 clinical_pdd=66.4, volt_high=300, volt_low=150, m_raw=(1, 2),
                 m_opp=(1, 2), m_low=(1, 2), mu=200, i_50=4, k_ecal=None, m_plus=None,
                 tissue_correction=1.0):
        super().__init__(temp=temp, press=press, model=model, n_dw=n_dw, p_elec=p_elec,
                         volt_high=volt_high, volt_low=volt_low, m_raw=m_raw,
                         m_opp=m_opp, m_low=m_low, clinical_pdd=clinical_pdd, mu=mu,
                         i_50=i_50, k_ecal=k_ecal, m_plus=m_plus, tissue_correction=tissue_correction)

    @property
    def r_50(self):
        """Depth of the 50% dose value."""
        return r_50(self.i_50)

    @property
    def dref(self):
        """Depth of the reference point."""
        return d_ref(self.i_50)

    @property
    def pq_gr(self):
        """The gradient correction of the electron beam."""
        return pq_gr(self.m_plus, self.m_raw)

    @property
    def kp_r50(self):
        """K'R50 value for cylindrical chambers."""
        return kp_r50(self.r_50)

    @property
    def dose_mu_dref(self):
        """cGy/MU at the depth of Dref."""
        return self.tissue_correction * self.m_corrected * self.pq_gr * self.kp_r50 * self.k_ecal * self.n_dw / self.mu

    @property
    def dose_mu_dmax(self):
        """cGy/MU at the depth of dmax."""
        return self.dose_mu_dref / (self.clinical_pdd / 100)
