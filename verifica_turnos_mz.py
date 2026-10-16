import pgsql
import pandas
import datetime
import locale

FISCALIAS = [
    "PUERTO MONTT",
    "CASTRO",
    "OSORNO",
    "PUERTO VARAS",
    "SACFI LL",
    "ANCUD",
    "CALBUCO",
    "MAULLIN",
    "QUELLÓN",
    "RÍO NEGRO"
]

def verifica_turnos_mz():
    sql = ''
    for i in range(0, 18):
        sql += (f'\nSELECT current_date+{i} fecha, fiscalia.id, fiscalia.nombre FROM fiscalia LEFT JOIN (select '
                f'id_fiscalia from turno_acd where current_date+{i} between fecha_hora_inicio::date and '
                f'fecha_hora_fin::date) turnos_ingresados ON (turnos_ingresados.id_fiscalia = fiscalia.id) WHERE '
                f'fiscalia.id not in (10) and fiscalia.estado=1 and turnos_ingresados.id_fiscalia is NULL UNION')
    sql = sql[:-6] + ' order by 1,3'
    sin_turno = pgsql.Pgsql(dbname='macro_zona', sql=sql, fetch=True).get_res()
    # print(sql)
    fiscalias, fecha_anterior = [], None
    print('TURNOS MZ FALTANTES:', end='')
    for st in sin_turno:
        fecha = st[0]
        if fecha != fecha_anterior:
            elementos_del_dia = [item[2] for item in sin_turno if item[0] == fecha]
            print(f'\n{(fecha.strftime("%A %d-%m-%Y")+":").ljust(21)} {", ".join(elementos_del_dia)}', end='')
        fecha_anterior = fecha
    print()


def verifica_turnos_fiscales():
    excel = ('C:\\Users\\mtrujillo\\OneDrive\\OneDrive - Ministerio Publico Gobierno Central\\Turno de instrucciones\\Turno Macrozona Sur 2024+2025 - X+XI+XII.xlsx')
    turno_fiscales = pandas.read_excel(excel)
    tf = turno_fiscales.to_numpy()
    print("\nFISCALES NO REGISTRADOS:")
    hoy = datetime.date.today()
    semana = datetime.date.today() + datetime.timedelta(days=21)
    for f in tf:
        if isinstance(f[2], pandas.Timestamp) and hoy <= f[2].date() <= semana:
            pass
            if isinstance(f[4], str) and len(f[4]) <= 3:
                print(f'{f[2].date().strftime("%A %d-%m-%Y")}\t|\t{f[3]}\t|\tSIN FISCAL\t|\t{f[4]}\t')


if __name__ == "__main__":
    locale.setlocale(locale.LC_TIME, "Spanish")
    verifica_turnos_mz()
    verifica_turnos_fiscales()
