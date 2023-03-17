import psycopg2
import requests
import json
from itertools import islice, chain
from time import sleep

CONTEST_COUNT = 10

TOKEN = os.environ['BOT_TOKEN']
DB_HOST = os.environ['DB_HOST']
DB = os.environ['POSTGRES_DB']
USER = os.environ['POSTGRES_USER']
PWD = os.environ['POSTGRES_PASSWORD']

print("request ->")
status_code = 0
while status_code != 200:
    try:
        r = requests.get("https://codeforces.com/api/problemset.problems")
        status_code = r.status_code
    except Exception as e: 
        print("Connection failed!\n", e)

all_json = json.loads(r.text)

while True:    
    try:
        con = psycopg2.connect(database=DB, user=USER, password=PWD, host=DB_HOST)
        con = psycopg2.connect(database="codeforces", user="pwd", password="pwd", host="postgres")
        cur = con.cursor()
    except Exception as e:
        print("DB failed!\n", e)
        continue
    break

cur.execute(f"SELECT SiteId, SiteIndex FROM Problems")
existing_problems = cur.fetchall()

problems_new = list()

for id, problem in enumerate(all_json["result"]["problems"]):
    # select only problems that have rating and tags fields
    if problem.get("rating", False) and problem.get("tags", False):
        problem["solvedCount"] = all_json["result"]["problemStatistics"][id]["solvedCount"]
        problem_site_id = (problem["contestId"], problem["index"])
#        if problem_site_id not in existing_problems:
        problems_new.append(problem)
print(len(problems_new))

#problems_list = problems_list[:8001]

tup = ((p["contestId"],p["index"],p["name"],p["solvedCount"],p["rating"],p["tags"]) for p in problems_new)
args_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s,%s)", x).decode('utf-8') for x in tup)
#cur.execute("INSERT INTO Problems VALUES " + args_str)

print("insert problems ->")
sql_query = f'''
    INSERT INTO Problems (SiteId, SiteIndex, Name, SolvedCount, Rating, Tags) 
    VALUES  {args_str}
    ON CONFLICT (SiteId, SiteIndex) DO UPDATE SET SolvedCount = EXCLUDED.SolvedCount
'''
#problem["db_id"] = sql_problem_id
if args_str:
    cur.execute(sql_query)
    print("finish insert problems ->")
con.commit()

sql_query = '''
    UPDATE
'''
print("finish")

fill_contests_sql = '''
CREATE TEMP TABLE IF NOT EXISTS temp_info  AS (
    with tags_list(tag) as (
        select distinct unnest(tags) from Problems where tags <> '{}'
    ),
    contest_types as (
        select distinct t.tag, p.rating
        from Problems p
        left outer join tags_list t on t.tag = any(p.tags)
        group by t.tag, p.rating
        having count(*) > 9
    ),
    contest_candidates as (
        select 
            p.Id,
            c.Tag,
            c.Rating,
            row_number() over (partition by c.tag, c.rating) as num,
            count(*) over (partition by c.tag, c.rating) as col
        from contest_types c
        left outer join problems p on c.tag = any(p.tags) and c.rating = p.rating
        ORDER BY c.tag, c.rating
    ),
    contest_info as (
        select *, ((row_number() over () - 1) /10)::int + 1 as chunk 
        from contest_candidates
        where num < col / 10 * 10 + 1
    )
    select * from contest_info
);

WITH ins AS (
    insert into contests
    select distinct chunk as id, tag, rating 
    from temp_info
    order by tag, rating asc
    on conflict do nothing
    returning id
)

insert into contestinfo
select chunk, id 
from temp_info
where chunk in (select * from ins)
order by tag, rating asc
on conflict do nothing;

DROP TABLE temp_info;
'''
cur.execute(fill_contests_sql)
con.commit()
sql = '''
SELECT count(*) FROM Problems
'''
cur.execute(sql)
print(len(cur.fetchall()))
sleep(5)
cur.execute(f"SELECT * FROM Problems")
print(len(cur.fetchall()))
#print(existing_problems[:3])
cur.execute(f"SELECT * FROM Contests")
print(len(cur.fetchall()))
cur.execute(f"SELECT * FROM ContestInfo")
print(len(cur.fetchall()))
#print(problems_list[index])

print("==========")
#cur.execute(f"SELECT * FROM Contests WHERE Id = 5")
#print(cur.fetchall())
"""
sql_query = '''
    SELECT *
    FROM Problems 
    WHERE Id IN (SELECT ProblemId FROM ContestInfo WHERE ContestId = 5)
'''
"""
#cur.execute(sql_query)
#selected = cur.fetchall()
#print(tag, selected)
#print all_json["result"]["problemStatistics"][index]
con.commit()
con.close()

#print(tags)
#print(ratings)
