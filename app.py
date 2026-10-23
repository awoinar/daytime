from datetime import date, datetime, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from daytime import ORAS_IMPLICIT, ORASE, calculeaza


def hhmm(td: timedelta) -> str:
    total_min = int(td.total_seconds() // 60)
    abs_min = abs(total_min)
    semn = "+" if total_min >= 0 else "-"
    return f"{semn}{abs_min // 60}h {abs_min % 60:02d}m"


# Streamlit uses desktop font sizes on phones too. 640px is its own phone breakpoint.
# The root font size is left alone: the date input must stay at 16px, or iOS Safari
# zooms the page when it gets focus. The 4.5rem top padding clears the 3.75rem header.
STIL_MOBIL = """
<style>
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] { padding-top: 4.5rem; }
    [data-testid="stHeading"] h1 { font-size: 1.75rem; }
    [data-testid="stHeading"] h3 { font-size: 1.25rem; }
    [data-testid="stMetricValue"] { font-size: 1.75rem; }
}
</style>
"""

st.set_page_config(page_icon="☀️", layout="centered")
st.html(STIL_MOBIL)
titlu = st.empty()

chei_orase = list(ORASE)
c_oras, c_zi = st.columns(2)
cheie_oras = c_oras.selectbox(
    "Oraș",
    chei_orase,
    index=chei_orase.index(ORAS_IMPLICIT),
    format_func=lambda cheie: ORASE[cheie].name,
)
oras = ORASE[cheie_oras]
# The container's TZ is Bucharest; "today" must be the chosen city's date.
zi = c_zi.date_input("Alege ziua", value=datetime.now(oras.tzinfo).date(), format="YYYY-MM-DD")
info = calculeaza(zi, oras)

st.set_page_config(page_title=f"Daylight — {oras.name}")
titlu.title(f"☀️ Daylight — {oras.name}")

ore = info.durata.seconds // 3600
minute = (info.durata.seconds % 3600) // 60
dif_sec_ieri = int(info.dif_fata_de_ieri.total_seconds())
abs_sec_ieri = abs(dif_sec_ieri)
semn_ieri = "+" if dif_sec_ieri >= 0 else "-"
delta_ieri_str = f"{semn_ieri}{abs_sec_ieri // 60}:{abs_sec_ieri % 60:02d}"

c1, c2, c3 = st.columns(3)
c1.metric("Răsărit", info.rasarit.strftime("%H:%M"))
c2.metric("Apus", info.apus.strftime("%H:%M"))
c3.metric(
    "Lungime zi",
    f"{ore}h {minute}min",
    delta=f"{delta_ieri_str} față de ieri",
)

c4, c5 = st.columns(2)
c4.metric("Față de 21 iun", hhmm(info.dif_fata_de_solst_vara))
c5.metric("Față de 21 dec", hhmm(info.dif_fata_de_solst_iarna))


@st.cache_data(show_spinner="Calculez curba anuală…")
def curba_anuala(cheie_oras: str, an: int) -> pd.DataFrame:
    oras = ORASE[cheie_oras]
    inceput = date(an, 1, 1)
    nr_zile = (date(an + 1, 1, 1) - inceput).days
    zile = [inceput + timedelta(days=i) for i in range(nr_zile)]
    secunde = [int(calculeaza(z, oras).durata.total_seconds()) for z in zile]
    sec_prev = int(calculeaza(inceput - timedelta(days=1), oras).durata.total_seconds())
    delta_sec = [s - (secunde[i - 1] if i > 0 else sec_prev) for i, s in enumerate(secunde)]
    ore = [s / 3600 for s in secunde]
    ore_hhmm = [f"{s // 3600}:{(s % 3600) // 60:02d}" for s in secunde]
    delta_min = [d / 60 for d in delta_sec]
    delta_str = [
        f"{'+' if d >= 0 else '-'}{abs(d) // 60}:{abs(d) % 60:02d}" for d in delta_sec
    ]
    return pd.DataFrame(
        {
            "data": zile,
            "ore": ore,
            "ore_hhmm": ore_hhmm,
            "delta_min": delta_min,
            "delta_str": delta_str,
        }
    )


df = curba_anuala(cheie_oras, zi.year)
sec_zi = int(info.durata.total_seconds())
selectie = pd.DataFrame({
    "data": [zi],
    "ore": [sec_zi / 3600],
    "ore_hhmm": [f"{sec_zi // 3600}:{(sec_zi % 3600) // 60:02d}"],
})

linia = (
    alt.Chart(df)
    .mark_line(color="#f59e0b")
    .encode(
        x=alt.X("data:T", title=None),
        y=alt.Y("ore:Q", title="Ore de lumină", scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip("data:T", title="Data"), alt.Tooltip("ore_hhmm:N", title="Lungime")],
    )
)
punct = (
    alt.Chart(selectie)
    .mark_circle(size=160, color="#dc2626")
    .encode(
        x="data:T",
        y="ore:Q",
        tooltip=[alt.Tooltip("data:T", title="Data"), alt.Tooltip("ore_hhmm:N", title="Lungime")],
    )
)

st.subheader(f"Curba anuală {zi.year}")
afiseaza_var = st.checkbox("Arată variația zilnică (min/zi)", value=False)

if afiseaza_var:
    linia_var = (
        alt.Chart(df)
        .mark_line(color="#0ea5e9")
        .encode(
            x="data:T",
            y=alt.Y(
                "delta_min:Q",
                title="Variație (min/zi)",
                axis=alt.Axis(orient="right"),
            ),
            tooltip=[
                alt.Tooltip("data:T", title="Data"),
                alt.Tooltip("delta_str:N", title="Variație"),
            ],
        )
    )
    chart = alt.layer(alt.layer(linia, punct), linia_var).resolve_scale(y="independent")
else:
    chart = linia + punct

st.altair_chart(chart, width="stretch")


def minute_din_miezul_noptii(dt) -> float:
    return dt.hour * 60 + dt.minute + dt.second / 60


rasarit_min = minute_din_miezul_noptii(info.rasarit)
apus_min = minute_din_miezul_noptii(info.apus)
rasarit_str = info.rasarit.strftime("%H:%M")
apus_str = info.apus.strftime("%H:%M")
strip_df = pd.DataFrame(
    [
        {"segment": "Noapte", "ordine": 0, "start": 0, "end": rasarit_min, "rasarit": rasarit_str, "apus": apus_str},
        {"segment": "Zi", "ordine": 1, "start": rasarit_min, "end": apus_min, "rasarit": rasarit_str, "apus": apus_str},
        {"segment": "Noapte", "ordine": 2, "start": apus_min, "end": 1440, "rasarit": rasarit_str, "apus": apus_str},
    ]
)
ticks = [0, 360, 720, 1080, 1440]

strip = (
    alt.Chart(strip_df)
    .mark_bar(height=40)
    .encode(
        x=alt.X(
            "start:Q",
            title=None,
            scale=alt.Scale(domain=[0, 1440]),
            axis=alt.Axis(values=ticks, labelExpr="datum.value/60 + 'h'"),
        ),
        x2="end:Q",
        color=alt.Color(
            "segment:N",
            scale=alt.Scale(domain=["Noapte", "Zi"], range=["#1e293b", "#fcd34d"]),
            legend=None,
        ),
        order="ordine:O",
        tooltip=["rasarit:N", "apus:N"],
    )
    .properties(height=110)
)

st.subheader("Ziua într-un interval de 24h")
st.altair_chart(strip, width="stretch")
