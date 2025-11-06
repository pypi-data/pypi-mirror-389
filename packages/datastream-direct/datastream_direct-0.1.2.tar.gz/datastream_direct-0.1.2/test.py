from datastream_direct.connection import connect
from datastream_direct.pandas_extras import fetch_frame

connection = connect(
    username="mhatfield@energydomain.com",
    password="Shermanh12!",
    host="data-staging-api.energydomain.com",
    port=443,
    database="energy_domain",
)

cursor = connection.cursor()
df = fetch_frame(cursor, "SELECT * from well_combined limit 100")
print(df)

connection.close()
