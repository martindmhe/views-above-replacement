from fastapi import FastAPI
import pickle
from fastapi import Request


import pandas as pd

app = FastAPI()

with open("saved_models/model.pkl", "rb") as f:
    model = pickle.load(f)

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

"""
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"is_loss": 1, "goal_differential": -4, "total_goals": 8, "max_leafs_blown_leads": 1, "goals_against_while_leading": 2, "leafs_streak": -6}'
"""

@app.post("/predict")
async def predict(request: Request):
    data = await request.json()
    # Single object → one row; list of objects → multiple rows
    rows = [data] if isinstance(data, dict) else data
    df = pd.DataFrame(rows)


    return {"prediction": model.predict(df)[0]}
    
