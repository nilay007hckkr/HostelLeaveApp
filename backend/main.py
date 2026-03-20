from fastapi import FastAPI

# This initializes your app
app = FastAPI()

# This is a "Route" (a destination your app can talk to)
@app.get("/")
def read_root():
    return {"message": "Welcome to the Hostel Leave App Backend, Nilay!"}

@app.get("/status")
def check_status():
    return {"status": "Server is running perfectly."}