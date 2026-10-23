from dataclasses import dataclass
from datetime import date, datetime, timedelta
from astral import LocationInfo
from astral.sun import sun
import sys

# The keys are ASCII because the app stores the chosen one in a cookie.
# Berlin and Freiburg coordinates are from their Wikipedia infoboxes.
ORASE: dict[str, LocationInfo] = {
    "bucuresti": LocationInfo("București", "România", "Europe/Bucharest", 44.4268, 26.1025),
    "berlin": LocationInfo("Berlin", "Germania", "Europe/Berlin", 52.5200, 13.4050),
    "freiburg": LocationInfo("Freiburg", "Germania", "Europe/Berlin", 47.9950, 7.8500),
}
ORAS_IMPLICIT = "bucuresti"


@dataclass
class InfoZi:
    data: date
    rasarit: datetime
    apus: datetime
    durata: timedelta
    dif_fata_de_ieri: timedelta
    dif_fata_de_solst_vara: timedelta
    dif_fata_de_solst_iarna: timedelta
    durata_solst_vara: timedelta
    durata_solst_iarna: timedelta


def ore_min(td: timedelta) -> str:
    total_min = int(td.total_seconds() // 60)
    return f"{total_min // 60}h {total_min % 60}min"


def calculeaza(data: date, oras: LocationInfo) -> InfoZi:
    s = sun(oras.observer, date=data, tzinfo=oras.timezone)
    rasarit = s['sunrise']
    apus = s['sunset']
    durata = apus - rasarit

    s_ieri = sun(oras.observer, date=date.fromordinal(data.toordinal() - 1), tzinfo=oras.timezone)
    durata_ieri = s_ieri['sunset'] - s_ieri['sunrise']

    solst_vara = sun(oras.observer, date=date(data.year, 6, 21), tzinfo=oras.timezone)
    solst_iarna = sun(oras.observer, date=date(data.year, 12, 21), tzinfo=oras.timezone)
    max_durata = solst_vara['sunset'] - solst_vara['sunrise']
    min_durata = solst_iarna['sunset'] - solst_iarna['sunrise']

    return InfoZi(
        data=data,
        rasarit=rasarit,
        apus=apus,
        durata=durata,
        dif_fata_de_ieri=durata - durata_ieri,
        dif_fata_de_solst_vara=durata - max_durata,
        dif_fata_de_solst_iarna=durata - min_durata,
        durata_solst_vara=max_durata,
        durata_solst_iarna=min_durata,
    )


def info_zi(data: date, oras: LocationInfo):
    info = calculeaza(data, oras)

    dif_sec = int(info.dif_fata_de_ieri.total_seconds())
    abs_sec = abs(dif_sec)
    dif_min = abs_sec // 60
    dif_rem = abs_sec % 60
    semn = '+' if dif_sec >= 0 else '-'

    print(f"\n=== {info.data.strftime('%d %B %Y')} - {oras.name} ===")
    print(f"Răsărit: {info.rasarit:%H:%M}")
    print(f"Apus: {info.apus:%H:%M}")
    print(f"Lungime: {ore_min(info.durata)}")
    print(f"Față de ieri: {semn}{dif_min} min, {dif_rem} secunde")
    print(f"Față de ziua max 21 iun ({ore_min(info.durata_solst_vara)}): "
          f"{int(info.dif_fata_de_solst_vara.total_seconds() // 60)} min")
    print(f"Față de ziua min 21 dec ({ore_min(info.durata_solst_iarna)}): "
          f"+{int(info.dif_fata_de_solst_iarna.total_seconds() // 60)} min")


if __name__ == "__main__":
    oras_cli = ORASE[ORAS_IMPLICIT]
    if len(sys.argv) == 1:
        info_zi(date.today(), oras_cli)
    else:
        try:
            data_introdusa = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
            info_zi(data_introdusa, oras_cli)
        except ValueError:
            print("Format greșit. Folosește: ziua.exe sau ziua.exe 2026-12-25")
    input("\nApasă Enter să închizi...")
