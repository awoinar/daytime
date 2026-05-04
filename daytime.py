from dataclasses import dataclass
from datetime import date, datetime, timedelta
from astral import LocationInfo
from astral.sun import sun
import sys

oras = LocationInfo("Bucharest", "Romania", "Europe/Bucharest", 44.4268, 26.1025)


@dataclass
class InfoZi:
    data: date
    rasarit: datetime
    apus: datetime
    durata: timedelta
    dif_fata_de_ieri: timedelta
    dif_fata_de_solst_vara: timedelta
    dif_fata_de_solst_iarna: timedelta


def calculeaza(data: date) -> InfoZi:
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
    )


def info_zi(data: date):
    info = calculeaza(data)
    ore = info.durata.seconds // 3600
    minute = (info.durata.seconds % 3600) // 60

    dif_sec = int(info.dif_fata_de_ieri.total_seconds())
    abs_sec = abs(dif_sec)
    dif_min = abs_sec // 60
    dif_rem = abs_sec % 60
    semn = '+' if dif_sec >= 0 else '-'

    print(f"\n=== {info.data.strftime('%d %B %Y')} - București ===")
    print(f"Răsărit: {info.rasarit:%H:%M}")
    print(f"Apus: {info.apus:%H:%M}")
    print(f"Lungime: {ore}h {minute}min")
    print(f"Față de ieri: {semn}{dif_min} min, {dif_rem} secunde")
    print(f"Față de ziua max 21 iun: {int(info.dif_fata_de_solst_vara.total_seconds() // 60)} min")
    print(f"Față de ziua min 21 dec: +{int(info.dif_fata_de_solst_iarna.total_seconds() // 60)} min")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        info_zi(date.today())
    else:
        try:
            data_introdusa = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
            info_zi(data_introdusa)
        except ValueError:
            print("Format greșit. Folosește: ziua.exe sau ziua.exe 2026-12-25")
    input("\nApasă Enter să închizi...")
