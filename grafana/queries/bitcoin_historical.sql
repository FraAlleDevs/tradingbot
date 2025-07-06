SELECT 
  "timestamp" AS "time", 
  close
FROM 
  btc_historical 
WHERE 
  ($__from/1000) < "timestamp" AND "timestamp" < ($__to/1000)