import psycopg2


class Pgsql:
    def __init__(self, dbname, sql, fetch):
        self.conn = psycopg2.connect(dbname=dbname, user='postgres', password='postgres', host='172.17.163.6', port='5432')
        self.curs = self.conn.cursor()
        self.curs.execute(sql)
        if fetch:
            self.resultado = self.curs.fetchall()
        else:
            self.conn.commit()
        self.curs.close()
        self.conn.close()

    def get_res(self):
        return self.resultado
