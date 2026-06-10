"""Pruebas estadisticas no parametricas para el estudio descriptivo y pruebas no paramétricas.

Implementa:
  * Correlacion de rangos de Spearman (rho)   -> modulo Senas a Texto.
  * Prueba U de Mann-Whitney + correlacion rango-biserial (tamano del efecto)
    -> modulo Texto a Senas.

Se apoya en ``scipy.stats``. Las inferencias se basan en rangos y medianas,
no en medias aritmeticas, tal como exige la naturaleza ordinal/dicotomica de
los datos (Corder & Foreman, 2014; Field, 2024).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

from ..config import ALPHA


@dataclass
class TestResult:
    """Resultado generico de una prueba estadistica.

    Attributes:
        title: Nombre legible de la prueba.
        summary: Tabla resumen (metricas principales) lista para exportar.
        detail: Tabla de apoyo (descriptivos por grupo, n, etc.).
        interpretation: Texto interpretativo de la decision estadistica.
    """

    title: str
    summary: pd.DataFrame
    detail: pd.DataFrame = field(default_factory=pd.DataFrame)
    interpretation: str = ""
    simple_conclusion: str = ""


def _significance_label(p_value: float, alpha: float) -> str:
    return "SIGNIFICATIVO" if p_value < alpha else "NO significativo"


def _interpret_strength(value: float) -> str:
    """Interpreta la magnitud de una correlacion segun su valor absoluto."""
    a = abs(value)
    if a < 0.10:
        return "insignificante"
    if a < 0.30:
        return "debil"
    if a < 0.50:
        return "moderada"
    if a < 0.70:
        return "fuerte"
    return "muy fuerte"


# Numero de remuestreos para los p-valores exactos por permutaciones.
PERM_RESAMPLES = 9999


def _perm_pvalue(statistic, samples, permutation_type, alternative, n_resamples=PERM_RESAMPLES):
    """Calcula un p-valor exacto por permutaciones con ``scipy.stats``.

    Si el numero total de permutaciones posibles es menor que ``n_resamples``,
    scipy enumera de forma exacta; de lo contrario realiza un muestreo Monte
    Carlo reproducible (semilla fija). Util para muestras pequenas, donde la
    aproximacion asintotica es imprecisa.
    """
    res = stats.permutation_test(
        samples,
        statistic,
        permutation_type=permutation_type,
        alternative=alternative,
        n_resamples=n_resamples,
        random_state=42,
    )
    return float(res.pvalue)


def _insert_after(summary: pd.DataFrame, after_metric: str, metric: str, value) -> pd.DataFrame:
    """Inserta una fila (Metrica, Valor) justo despues de ``after_metric``."""
    matches = summary.index[summary["Metrica"] == after_metric]
    pos = (int(matches[0]) + 1) if len(matches) else len(summary)
    extra = pd.DataFrame({"Metrica": [metric], "Valor": [value]})
    return pd.concat(
        [summary.iloc[:pos], extra, summary.iloc[pos:]], ignore_index=True
    )


def spearman_correlation(
    df: pd.DataFrame,
    col_x: str,
    col_y: str,
    alpha: float = ALPHA,
    context: str = "",
    exact: bool = False,
) -> TestResult:
    """Calcula la correlacion de rangos de Spearman entre dos columnas.

    Aplica tanto para asociacion entre una variable ordinal y una continua
    como entre dos variables ordinales (ambos casos validos para Spearman, ya
    que se basa en rangos). ``context`` se usa solo para titular el resultado.

    Si ``exact`` es True, ademas del p-valor asintotico se calcula un p-valor
    exacto por permutaciones (recomendado para muestras pequenas) y la decision
    se basa en este ultimo.
    """
    data = df[[col_x, col_y]].apply(pd.to_numeric, errors="coerce").dropna()
    n = len(data)
    if n < 3:
        raise ValueError(
            "Se requieren al menos 3 pares de datos validos para Spearman."
        )

    rho, p_value = stats.spearmanr(data[col_x], data[col_y])
    direccion = "positiva" if rho >= 0 else "negativa"
    fuerza = _interpret_strength(rho)

    p_exact = None
    if exact:
        p_exact = _perm_pvalue(
            lambda a, b: stats.spearmanr(a, b).statistic,
            (data[col_x].to_numpy(), data[col_y].to_numpy()),
            permutation_type="pairings",
            alternative="two-sided",
        )
    decision_p = p_exact if p_exact is not None else p_value
    significativo = decision_p < alpha

    summary = pd.DataFrame(
        {
            "Metrica": [
                "Prueba",
                "Variable X",
                "Variable Y",
                "N (pares validos)",
                "Coeficiente Spearman (rho)",
                "Valor p",
                "Nivel de significancia (alpha)",
                "Decision",
            ],
            "Valor": [
                "Correlacion de rangos de Spearman",
                col_x,
                col_y,
                n,
                round(float(rho), 4),
                round(float(p_value), 4),
                alpha,
                _significance_label(decision_p, alpha),
            ],
        }
    )
    if p_exact is not None:
        summary = _insert_after(
            summary, "Valor p", "Valor p exacto (permutaciones)", round(p_exact, 4)
        )

    detail = pd.DataFrame(
        {
            "Estadistico": [
                f"Mediana {col_x}",
                f"Mediana {col_y}",
                f"Media {col_x}",
                f"Media {col_y}",
                "Direccion de la asociacion",
                "Fuerza de la asociacion",
            ],
            "Valor": [
                round(float(data[col_x].median()), 4),
                round(float(data[col_y].median()), 4),
                round(float(data[col_x].mean()), 4),
                round(float(data[col_y].mean()), 4),
                direccion,
                fuerza,
            ],
        }
    )

    p_txt = (
        f"valor p exacto = {decision_p:.4f} (permutaciones)"
        if p_exact is not None
        else f"valor p = {decision_p:.4f}"
    )
    if significativo:
        interp = (
            f"Con un nivel de significancia alpha = {alpha}, se obtuvo rho = "
            f"{rho:.4f} y un {p_txt} (p < {alpha}). Se RECHAZA "
            f"la hipotesis nula: existe una correlacion {direccion} y "
            f"estadisticamente significativa entre '{col_x}' y '{col_y}'. "
            f"La fuerza de la asociacion es {fuerza}. A mayor valoracion en una "
            f"variable, {'mayor' if rho >= 0 else 'menor'} valoracion en la otra."
        )
    else:
        interp = (
            f"Con un nivel de significancia alpha = {alpha}, se obtuvo rho = "
            f"{rho:.4f} y un {p_txt} (p >= {alpha}). NO se "
            f"rechaza la hipotesis nula: no hay evidencia estadistica "
            f"suficiente para afirmar una correlacion entre '{col_x}' y "
            f"'{col_y}'."
        )

    if significativo:
        tendencia = "tambien sube" if rho >= 0 else "tiende a bajar"
        simple = (
            f"SI existe correlacion entre '{col_x}' y '{col_y}'. La relacion es "
            f"{direccion} y de fuerza {fuerza}: cuando una sube, la otra "
            f"{tendencia}."
        )
    else:
        simple = (
            f"NO existe correlacion entre '{col_x}' y '{col_y}'. No hay evidencia "
            f"de que una variable se relacione con la otra."
        )

    title = "Correlacion de Spearman"
    if context:
        title = f"{title} ({context})"
    return TestResult(
        title=title,
        summary=summary,
        detail=detail,
        interpretation=interp,
        simple_conclusion=simple,
    )


def group_comparison(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    alpha: float = ALPHA,
    exact: bool = False,
) -> TestResult:
    """Analisis por grupos: variable ordinal frente a una variable nominal.

    Compara las medianas de una variable ordinal (``value_col``) entre las
    categorias de una variable nominal (``group_col``) definida por el usuario.
    Es flexible respecto al numero de categorias de la nominal:

      * 2 categorias  -> Prueba U de Mann-Whitney + correlacion rango-biserial
        (tamano del efecto).
      * 3 o mas       -> Prueba H de Kruskal-Wallis + epsilon cuadrado
        (tamano del efecto).

    Si ``exact`` es True, agrega un p-valor exacto por permutaciones y basa la
    decision en este (recomendado para muestras pequenas o desbalanceadas).
    """
    work = df[[group_col, value_col]].copy()
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    work = work.dropna()

    groups = _split_groups(work, group_col)
    if len(groups) < 2:
        raise ValueError(
            f"La columna nominal '{group_col}' debe tener al menos 2 categorias "
            f"con datos. Encontradas: {len(groups)}."
        )

    arrays = {label: work.loc[idx, value_col].to_numpy() for label, idx in groups.items()}
    for label, arr in arrays.items():
        if len(arr) < 1:
            raise ValueError(f"El grupo '{label}' no tiene observaciones validas.")

    detail = pd.DataFrame(
        {
            "Grupo": [str(lbl) for lbl in arrays],
            "N": [len(arr) for arr in arrays.values()],
            "Mediana": [round(float(np.median(a)), 4) for a in arrays.values()],
            "Media": [round(float(np.mean(a)), 4) for a in arrays.values()],
            "Minimo": [float(np.min(a)) for a in arrays.values()],
            "Maximo": [float(np.max(a)) for a in arrays.values()],
        }
    )

    if len(groups) == 2:
        summary, interp, title, simple = _two_group_test(
            arrays, group_col, value_col, alpha, exact
        )
    else:
        summary, interp, title, simple = _k_group_test(
            arrays, group_col, value_col, alpha, exact
        )

    return TestResult(
        title=title,
        summary=summary,
        detail=detail,
        interpretation=interp,
        simple_conclusion=simple,
    )


def _two_group_test(arrays, group_col, value_col, alpha, exact=False):
    """U de Mann-Whitney + correlacion rango-biserial para 2 grupos."""
    labels = list(arrays.keys())
    g1_label, g2_label = labels[0], labels[1]
    g1, g2 = arrays[g1_label], arrays[g2_label]
    n1, n2 = len(g1), len(g2)

    u_stat, p_value = stats.mannwhitneyu(g1, g2, alternative="two-sided")
    rank_biserial = (2.0 * u_stat) / (n1 * n2) - 1.0
    fuerza = _interpret_strength(rank_biserial)

    p_exact = None
    if exact:
        p_exact = _perm_pvalue(
            lambda a, b: stats.mannwhitneyu(a, b, alternative="two-sided").statistic,
            (g1, g2),
            permutation_type="independent",
            alternative="two-sided",
        )
    decision_p = p_exact if p_exact is not None else p_value
    significativo = decision_p < alpha

    summary = pd.DataFrame(
        {
            "Metrica": [
                "Prueba",
                "Variable nominal (grupos)",
                "Variable ordinal evaluada",
                f"Grupo 1 ({g1_label})  n",
                f"Grupo 2 ({g2_label})  n",
                "Estadistico U",
                "Valor p",
                "Correlacion rango-biserial (tamano efecto)",
                "Magnitud del efecto",
                "Nivel de significancia (alpha)",
                "Decision",
            ],
            "Valor": [
                "U de Mann-Whitney + rango-biserial",
                group_col,
                value_col,
                n1,
                n2,
                round(float(u_stat), 4),
                round(float(p_value), 4),
                round(float(rank_biserial), 4),
                fuerza,
                alpha,
                _significance_label(decision_p, alpha),
            ],
        }
    )
    if p_exact is not None:
        summary = _insert_after(
            summary, "Valor p", "Valor p exacto (permutaciones)", round(p_exact, 4)
        )

    p_txt = (
        f"valor p exacto = {decision_p:.4f} (permutaciones)"
        if p_exact is not None
        else f"valor p = {decision_p:.4f}"
    )
    mediana_mayor = g1_label if np.median(g1) >= np.median(g2) else g2_label
    if significativo:
        interp = (
            f"Con alpha = {alpha} se obtuvo U = {u_stat:.2f} y un {p_txt} "
            f"(p < {alpha}). Se RECHAZA la hipotesis nula: las "
            f"medianas de '{value_col}' difieren significativamente entre los "
            f"grupos de '{group_col}'. El grupo '{mediana_mayor}' presenta la "
            f"mediana mas alta. El tamano del efecto (rango-biserial = "
            f"{rank_biserial:.4f}) indica una magnitud {fuerza}."
        )
    else:
        interp = (
            f"Con alpha = {alpha} se obtuvo U = {u_stat:.2f} y un {p_txt} "
            f"(p >= {alpha}). NO se rechaza la hipotesis nula: no "
            f"hay diferencias estadisticamente significativas entre las "
            f"medianas de los grupos. Tamano del efecto rango-biserial = "
            f"{rank_biserial:.4f} ({fuerza})."
        )
    if significativo:
        simple = (
            f"SI hay diferencia entre los grupos de '{group_col}'. El grupo "
            f"'{mediana_mayor}' tiende a calificar mas alto en '{value_col}'."
        )
    else:
        simple = (
            f"NO hay diferencia significativa en '{value_col}' entre los grupos "
            f"de '{group_col}'. Los grupos se comportan de forma parecida."
        )
    return summary, interp, "U de Mann-Whitney (Ordinal vs Nominal, 2 grupos)", simple


def _k_group_test(arrays, group_col, value_col, alpha, exact=False):
    """H de Kruskal-Wallis + epsilon cuadrado para 3 o mas grupos."""
    samples = list(arrays.values())
    n_total = sum(len(a) for a in samples)
    k = len(samples)

    h_stat, p_value = stats.kruskal(*samples)
    # Epsilon cuadrado (Tomczak & Tomczak, 2014): eps2 = H / (n - 1)
    epsilon_sq = float(h_stat) / (n_total - 1) if n_total > 1 else 0.0
    fuerza = _interpret_epsilon(epsilon_sq)

    p_exact = None
    if exact:
        # H solo crece con la separacion entre grupos -> prueba de cola superior.
        p_exact = _perm_pvalue(
            lambda *args: stats.kruskal(*args).statistic,
            tuple(samples),
            permutation_type="independent",
            alternative="greater",
        )
    decision_p = p_exact if p_exact is not None else p_value
    significativo = decision_p < alpha

    summary = pd.DataFrame(
        {
            "Metrica": [
                "Prueba",
                "Variable nominal (grupos)",
                "Variable ordinal evaluada",
                "Numero de grupos (k)",
                "N total",
                "Estadistico H",
                "Grados de libertad",
                "Valor p",
                "Epsilon cuadrado (tamano efecto)",
                "Magnitud del efecto",
                "Nivel de significancia (alpha)",
                "Decision",
            ],
            "Valor": [
                "H de Kruskal-Wallis + epsilon cuadrado",
                group_col,
                value_col,
                k,
                n_total,
                round(float(h_stat), 4),
                k - 1,
                round(float(p_value), 4),
                round(epsilon_sq, 4),
                fuerza,
                alpha,
                _significance_label(decision_p, alpha),
            ],
        }
    )
    if p_exact is not None:
        summary = _insert_after(
            summary, "Valor p", "Valor p exacto (permutaciones)", round(p_exact, 4)
        )

    p_txt = (
        f"valor p exacto = {decision_p:.4f} (permutaciones)"
        if p_exact is not None
        else f"valor p = {decision_p:.4f}"
    )
    medianas = {lbl: float(np.median(a)) for lbl, a in arrays.items()}
    grupo_top = max(medianas, key=medianas.get)
    if significativo:
        interp = (
            f"Con alpha = {alpha} se obtuvo H = {h_stat:.2f} (gl = {k - 1}) y un "
            f"{p_txt} (p < {alpha}). Se RECHAZA la hipotesis "
            f"nula: al menos un grupo de '{group_col}' presenta una mediana de "
            f"'{value_col}' distinta. El grupo '{grupo_top}' muestra la mediana "
            f"mas alta. El tamano del efecto (epsilon cuadrado = {epsilon_sq:.4f}) "
            f"es {fuerza}."
        )
    else:
        interp = (
            f"Con alpha = {alpha} se obtuvo H = {h_stat:.2f} (gl = {k - 1}) y un "
            f"{p_txt} (p >= {alpha}). NO se rechaza la hipotesis "
            f"nula: no hay diferencias significativas entre las medianas de los "
            f"grupos. Tamano del efecto epsilon cuadrado = {epsilon_sq:.4f} "
            f"({fuerza})."
        )
    if significativo:
        simple = (
            f"SI hay diferencias entre los grupos de '{group_col}'. El grupo "
            f"'{grupo_top}' tiende a calificar mas alto en '{value_col}'."
        )
    else:
        simple = (
            f"NO hay diferencias significativas en '{value_col}' entre los grupos "
            f"de '{group_col}'. Todos los grupos se comportan de forma parecida."
        )
    return summary, interp, "H de Kruskal-Wallis (Ordinal vs Nominal, 3+ grupos)", simple


def _interpret_epsilon(value: float) -> str:
    """Interpreta epsilon cuadrado (convenciones tipo eta cuadrado)."""
    if value < 0.01:
        return "insignificante"
    if value < 0.08:
        return "pequeno"
    if value < 0.26:
        return "moderado"
    return "grande"


def _interpret_cramer(value: float) -> str:
    """Interpreta V de Cramer con umbrales generales (Cohen)."""
    if value < 0.10:
        return "insignificante"
    if value < 0.30:
        return "pequena"
    if value < 0.50:
        return "moderada"
    return "grande"


def categorical_association(
    df: pd.DataFrame,
    col_a: str,
    col_b: str,
    alpha: float = ALPHA,
    n_resamples: int = PERM_RESAMPLES,
) -> TestResult:
    """Asociacion entre dos variables categoricas/nominales.

    Funcionalidad independiente de las pruebas de rangos. En lugar de
    chi-cuadrado (poco fiable con frecuencias esperadas < 5, habitual en
    muestras pequenas) emplea pruebas exactas:

      * Tabla 2x2  -> Prueba exacta de Fisher.
      * Tabla rxc  -> Prueba exacta tipo Fisher-Freeman-Halton por simulacion
        Monte Carlo con margenes fijos (equivale a permutar el emparejamiento
        entre ambas variables).

    El tamano del efecto se reporta mediante la V de Cramer.
    """
    work = df[[col_a, col_b]].dropna()
    if len(work) < 3:
        raise ValueError("Se requieren al menos 3 observaciones validas.")

    a = work[col_a].astype(str)
    b = work[col_b].astype(str)
    table = pd.crosstab(a, b)
    if table.shape[0] < 2 or table.shape[1] < 2:
        raise ValueError(
            "Cada variable debe tener al menos 2 categorias para evaluar asociacion."
        )

    n = int(table.values.sum())
    chi2, _, dof, expected = stats.chi2_contingency(table.values, correction=False)
    r, c = table.shape
    cramer_v = float(np.sqrt(chi2 / (n * (min(r, c) - 1)))) if n > 0 else 0.0
    fuerza = _interpret_cramer(cramer_v)
    min_expected = float(np.min(expected))

    if r == 2 and c == 2:
        _, p_value = stats.fisher_exact(table.values)
        metodo = "Prueba exacta de Fisher (tabla 2x2)"
    else:
        p_value = _chi2_perm_pvalue(a.to_numpy(), b.to_numpy(), n_resamples)
        metodo = "Prueba exacta de Monte Carlo (Fisher-Freeman-Halton, margenes fijos)"

    significativo = p_value < alpha

    summary = pd.DataFrame(
        {
            "Metrica": [
                "Prueba",
                "Variable A",
                "Variable B",
                "N total",
                "Dimensiones de la tabla",
                "Frecuencia esperada minima",
                "Chi-cuadrado (referencia)",
                "Valor p exacto",
                "V de Cramer (tamano efecto)",
                "Magnitud de la asociacion",
                "Nivel de significancia (alpha)",
                "Decision",
            ],
            "Valor": [
                metodo,
                col_a,
                col_b,
                n,
                f"{r} x {c}",
                round(min_expected, 4),
                round(float(chi2), 4),
                round(float(p_value), 4),
                round(cramer_v, 4),
                fuerza,
                alpha,
                _significance_label(p_value, alpha),
            ],
        }
    )

    # La tabla de contingencia se entrega como detalle (con la categoria visible)
    detail = table.reset_index()

    nota_chi = ""
    if min_expected < 5:
        nota_chi = (
            " La frecuencia esperada minima es menor que 5, por lo que "
            "chi-cuadrado seria poco fiable; por eso se usa la prueba exacta."
        )
    if significativo:
        interp = (
            f"Con alpha = {alpha}, la {metodo.lower()} arrojo un valor p = "
            f"{p_value:.4f} (p < {alpha}). Se RECHAZA la hipotesis nula de "
            f"independencia: existe una asociacion estadisticamente "
            f"significativa entre '{col_a}' y '{col_b}'. La intensidad de la "
            f"asociacion (V de Cramer = {cramer_v:.4f}) es {fuerza}.{nota_chi}"
        )
    else:
        interp = (
            f"Con alpha = {alpha}, la {metodo.lower()} arrojo un valor p = "
            f"{p_value:.4f} (p >= {alpha}). NO se rechaza la hipotesis nula: no "
            f"hay evidencia de asociacion entre '{col_a}' y '{col_b}'. V de "
            f"Cramer = {cramer_v:.4f} ({fuerza}).{nota_chi}"
        )

    if significativo:
        simple = (
            f"SI hay asociacion entre '{col_a}' y '{col_b}': las dos variables "
            f"estan relacionadas (no son independientes). Intensidad {fuerza}."
        )
    else:
        simple = (
            f"NO hay asociacion entre '{col_a}' y '{col_b}': se comportan de "
            f"forma independiente."
        )

    return TestResult(
        title="Asociacion categorica (Fisher + V de Cramer)",
        summary=summary,
        detail=detail,
        interpretation=interp,
        simple_conclusion=simple,
    )


def _chi2_perm_pvalue(a, b, n_resamples: int = PERM_RESAMPLES) -> float:
    """P-valor exacto Monte Carlo para tablas rxc con margenes fijos.

    Permuta el emparejamiento entre las dos variables (preserva ambos
    totales marginales) y mide la proporcion de tablas con un estadistico
    chi-cuadrado igual o mayor al observado. Como los margenes quedan fijos, la
    frecuencia esperada es constante y el calculo es muy rapido.
    """
    a_codes = pd.factorize(a)[0]
    b_codes = pd.factorize(b)[0]
    r = int(a_codes.max()) + 1
    c = int(b_codes.max()) + 1
    n = len(a_codes)

    flat_obs = np.bincount(a_codes * c + b_codes, minlength=r * c).astype(float)
    obs = flat_obs.reshape(r, c)
    row = obs.sum(axis=1, keepdims=True)
    col = obs.sum(axis=0, keepdims=True)
    exp = row @ col / n

    def chi2_of(table: np.ndarray) -> float:
        return float(np.sum((table - exp) ** 2 / exp))

    observed_stat = chi2_of(obs)
    rng = np.random.default_rng(42)
    b_perm = b_codes.copy()
    count = 1  # incluye la tabla observada (correccion +1)
    for _ in range(n_resamples):
        rng.shuffle(b_perm)
        table = np.bincount(a_codes * c + b_perm, minlength=r * c).reshape(r, c)
        if chi2_of(table.astype(float)) >= observed_stat - 1e-9:
            count += 1
    return count / (n_resamples + 1)


def _split_groups(df: pd.DataFrame, group_col: str) -> dict[object, pd.Index]:
    """Agrupa el DataFrame por las categorias de una variable nominal.

    Acepta cualquier numero de categorias (>= 2). Si la variable es de tipo
    dicotomico (1/0, si/no, true/false) ordena el grupo "positivo" primero.
    """
    series = df[group_col]
    uniques = list(pd.unique(series.dropna()))

    def _rank(value: object):
        text = str(value).strip().lower()
        if text in {"1", "1.0", "si", "sí", "yes", "true", "verdadero"}:
            return (0, text)
        if text in {"0", "0.0", "no", "false", "falso"}:
            return (1, text)
        return (2, text)

    ordered = sorted(uniques, key=_rank)
    return {val: df.index[series == val] for val in ordered}
