import psycopg2
import pandas as pd
from datetime import datetime, timedelta, time


DB_HOST = "172.17.163.6"
DB_PORT = 5432
DB_NAME = "macro_zona"
DB_USER = "postgres"
DB_PASS = "postgres"


def monday_of_week(d):
    return d - timedelta(days=d.weekday())


def week_label(d):
    iso = d.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def day_span(d):
    s = datetime.combine(d, time(0, 0, 0))
    e = s + timedelta(days=1)
    return s, e


def fetch_future_turnos(conn):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, fecha_hora_inicio, fecha_hora_fin, juez, id_usuario,
               id_fiscalia, fiscal, tel_fiscal, tel_juez
        FROM turno_acd
        WHERE fecha_hora_inicio > NOW()::timestamp
        ORDER BY id_fiscalia, fecha_hora_inicio
        """
    )
    rows = cur.fetchall()
    cur.close()
    return pd.DataFrame(
        rows,
        columns=[
            "id", "fecha_hora_inicio", "fecha_hora_fin", "juez",
            "id_usuario", "id_fiscalia", "fiscal", "tel_fiscal", "tel_juez"
        ]
    )


def fetch_fiscalias(conn):
    cur = conn.cursor()
    cur.execute(
        "SELECT id AS id_fiscalia, nombre AS fiscalia_nombre "
        "FROM fiscalia "
        "WHERE id IN (1001, 1002, 1004, 1005, 1007, 1010, "
        "1011, 1014, 1015, 1016, 1017, 1018, 1031) "
        "ORDER BY id"
    )
    rows = cur.fetchall()
    cur.close()
    return pd.DataFrame(rows, columns=["id_fiscalia", "fiscalia_nombre"])


def build_weekly_grids(df_turnos, df_fiscalia):
    if not df_turnos.empty:
        for c in ["fecha_hora_inicio", "fecha_hora_fin"]:
            if not pd.api.types.is_datetime64_any_dtype(df_turnos[c]):
                df_turnos[c] = pd.to_datetime(df_turnos[c])
        df_turnos["fecha"] = df_turnos["fecha_hora_inicio"].dt.date
        df_turnos["lunes_semana"] = df_turnos["fecha"].apply(monday_of_week)
        weeks = sorted(df_turnos["lunes_semana"].unique())
    else:
        weeks = [monday_of_week(datetime.now().date())]

    week_to_grid = {}

    for week_monday in weeks:
        days = [week_monday + timedelta(days=i) for i in range(5)]
        day_labels = [
            f"{n} {d.strftime('%d/%m/%Y')}"
            for n, d in zip(["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"], days)
        ]
        ws = datetime.combine(week_monday, time(0, 0, 0))
        we = ws + timedelta(days=6)

        if not df_turnos.empty:
            df_w = df_turnos[
                (df_turnos["fecha_hora_fin"] > ws)
                & (df_turnos["fecha_hora_inicio"] < we)
            ]
        else:
            df_w = df_turnos.copy()

        id2name = dict(
            zip(df_fiscalia["id_fiscalia"], df_fiscalia["fiscalia_nombre"])
        )
        grid_df = pd.DataFrame(
            "", index=day_labels, columns=[id2name[i] for i in df_fiscalia["id_fiscalia"]]
        )

        if not df_w.empty:
            for di, d in enumerate(days):
                dc = day_labels[di]
                ds, de = day_span(d)
                hits = df_w[
                    (df_w["fecha_hora_fin"] > ds)
                    & (df_w["fecha_hora_inicio"] < de)
                ]
                for fiscalia_id, sub in hits.groupby("id_fiscalia"):
                    lines = []
                    for _, r in sub.iterrows():
                        f = (r["fiscal"] or "").strip()
                        tf = (str(r["tel_fiscal"]) if r["tel_fiscal"] else "").strip()
                        j = (r["juez"] or "").strip()
                        tj = (str(r["tel_juez"]) if r["tel_juez"] else "").strip()
                        lines.append(
                            f"{f if f else 'Fiscal s/d'} "
                            f"({tf if tf else 's/tel'}) | "
                            f"{j if j else 'Juez s/d'} "
                            f"({tj if tj else 's/tel'})"
                        )
                    fname = id2name.get(fiscalia_id)
                    if fname is not None:
                        grid_df.loc[dc, fname] = "\n".join(lines)

        week_to_grid[week_label(week_monday)] = (
            grid_df.reset_index().rename(columns={"index": "Fecha"})
        )

    return week_to_grid


def print_table(df):
    cols = list(df.columns)
    widths = {c: max(len(str(c)), *(len(str(x)) for x in df[c].tolist())) for c in cols}
    sep = "+" + "+".join("-" * (widths[c] + 2) for c in cols) + "+"
    header = "|" + "|".join(" " + c.ljust(widths[c]) + " " for c in cols) + "|"
    print(sep)
    print(header)
    print(sep)
    for _, r in df.iterrows():
        row = "|" + "|".join(
            " " + str(r[c]).ljust(widths[c]) + " " for c in cols
        ) + "|"
        print(row)
        print(sep)


def main():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    df_turnos = fetch_future_turnos(conn)
    df_fiscalia = fetch_fiscalias(conn)
    conn.close()
    week_to_grid = build_weekly_grids(df_turnos, df_fiscalia)
    for _, df in week_to_grid.items():
        print_table(df)


if __name__ == "__main__":
    main()
