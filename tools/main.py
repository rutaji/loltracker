import json
only_id = True

if __name__ == '__main__':
    with open('champion.json', 'r') as file:
        data = json.load(file)
    data = data["data"]
    for i in data.values():
        if only_id:
            print("""conn.execute(query, {"id": \"""" + i["id"] + """"})""")
        else:
            print("""conn.execute(query, {"id": \"""" + i["id"] + """\", "name": \"""" + i["name"] + """\"})""")

