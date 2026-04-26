from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
import psycopg, psycopg.rows, os, jwt, bcrypt
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL","postgresql://fleetuser:fleetpass@localhost:5432/fleetdb")
JWT_SECRET = os.getenv("JWT_SECRET","thp-ghana-fleet-secret")
app = FastAPI(title="THP Ghana Fleet API")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
security = HTTPBearer()
frontend_path = os.path.join(os.path.dirname(__file__),'..','frontend')

def get_conn():
    return psycopg.connect(DATABASE_URL, row_factory=psycopg.rows.dict_row)

def query(sql, params=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()

def query_one(sql, params=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()

def execute(sql, params=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            try: result=cur.fetchone(); conn.commit(); return result
            except: conn.commit(); return None

def create_token(uid, role):
    return jwt.encode({"sub":str(uid),"role":role,"exp":datetime.utcnow()+timedelta(hours=24)},JWT_SECRET,algorithm="HS256")

def get_current_user(credentials:HTTPAuthorizationCredentials=Depends(security)):
    try:
        p=jwt.decode(credentials.credentials,JWT_SECRET,algorithms=["HS256"])
        return {"id":int(p["sub"]),"role":p["role"]}
    except: raise HTTPException(status_code=401,detail="Invalid token")

def require_admin(user=Depends(get_current_user)):
    if user["role"] != "admin": raise HTTPException(status_code=403,detail="Admin required")
    return user

# ── Models ────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel): username:str; password:str

class VehicleCreate(BaseModel):
    unit_number:str; registration:Optional[str]=None; vin:Optional[str]=None; make:Optional[str]=None
    model:Optional[str]=None; year:Optional[int]=None; color:Optional[str]=None
    engine_number:Optional[str]=None; vehicle_type_id:Optional[int]=None
    fuel_type_id:Optional[int]=None; department_id:Optional[int]=None; group_id:Optional[int]=None
    tank_capacity:Optional[float]=None; current_odometer:Optional[int]=0
    purchase_date:Optional[str]=None; purchase_cost:Optional[float]=None; purchase_vendor_id:Optional[int]=None
    insurance_policy:Optional[str]=None; insurance_vendor_id:Optional[int]=None
    insurance_expiry:Optional[str]=None; insurance_cost:Optional[float]=None
    roadworthy_number:Optional[str]=None; roadworthy_expiry:Optional[str]=None; roadworthy_cost:Optional[float]=None
    notes:Optional[str]=None; photo_url:Optional[str]=None

class DriverCreate(BaseModel):
    employee_number:Optional[str]=None; first_name:str; last_name:str
    job_title:Optional[str]=None; email:Optional[str]=None; phone:Optional[str]=None
    department_id:Optional[int]=None; licence_number:Optional[str]=None
    licence_expiry:Optional[str]=None; licence_state:Optional[str]=None
    health_ref:Optional[str]=None; health_expiry:Optional[str]=None
    hire_date:Optional[str]=None; hourly_wage:Optional[float]=0; category_id:Optional[int]=None; service_type:Optional[str]=None; notes:Optional[str]=None; photo_url:Optional[str]=None

class FuelCardCreate(BaseModel):
    card_number:str; card_type:Optional[str]="GO CARD"
    vehicle_id:Optional[int]=None; driver_id:Optional[int]=None
    current_balance:Optional[float]=0; notes:Optional[str]=None

class FuelTxCreate(BaseModel):
    transaction_date:str; transaction_type:Optional[str]="purchase"
    vehicle_id:Optional[int]=None; driver_id:Optional[int]=None
    fuel_card_id:Optional[int]=None; transfer_to_card_id:Optional[int]=None
    fuel_type_id:Optional[int]=None; vendor_id:Optional[int]=None
    project_id:Optional[int]=None; location:Optional[str]=None
    trip_purpose:Optional[str]=None; odometer_start:Optional[int]=None; odometer_end:Optional[int]=None
    litres:Optional[float]=None; cost_per_litre:Optional[float]=None; total_cost:Optional[float]=None
    invoice_number:Optional[str]=None; reference:Optional[str]=None; is_full_tank:Optional[bool]=True

class TripCreate(BaseModel):
    vehicle_id:int; driver_id:Optional[int]=None; project_id:Optional[int]=None
    trip_date:str; departure_time:Optional[str]=None; return_time:Optional[str]=None
    origin:Optional[str]=None; destination:Optional[str]=None; purpose:str
    odometer_start:Optional[int]=None; odometer_end:Optional[int]=None
    passengers:Optional[int]=0; notes:Optional[str]=None

class MaintenanceCreate(BaseModel):
    vehicle_id:int; maintenance_type_id:Optional[int]=None; vendor_id:Optional[int]=None
    project_id:Optional[int]=None; service_date:str; odometer:Optional[int]=None
    description:str; technician:Optional[str]=None; labour_cost:Optional[float]=0
    parts_cost:Optional[float]=0; total_cost:Optional[float]=0
    invoice_number:Optional[str]=None; next_due_date:Optional[str]=None
    next_due_odometer:Optional[int]=None; notes:Optional[str]=None

class InsuranceCreate(BaseModel):
    vehicle_id:int; vendor_id:Optional[int]=None; project_id:Optional[int]=None
    policy_number:Optional[str]=None; start_date:str; expiry_date:str
    cost:Optional[float]=None; notes:Optional[str]=None

class RoadworthyCreate(BaseModel):
    vehicle_id:int; vendor_id:Optional[int]=None; project_id:Optional[int]=None
    certificate_number:Optional[str]=None; issue_date:str; expiry_date:str
    cost:Optional[float]=None; notes:Optional[str]=None

class VendorCreate(BaseModel):
    name:str; contact_person:Optional[str]=None; phone:Optional[str]=None
    email:Optional[str]=None; address:Optional[str]=None; category:Optional[str]=None; notes:Optional[str]=None

class ProjectCreate(BaseModel):
    code:str; name:str; description:Optional[str]=None
    start_date:Optional[str]=None; end_date:Optional[str]=None

class UserCreate(BaseModel):
    username:str; email:str; password:str; first_name:Optional[str]=None
    last_name:Optional[str]=None; role:Optional[str]="viewer"

class ReminderUpdate(BaseModel): status:str
class PasswordChange(BaseModel): password:str

# ── Frontend ──────────────────────────────────────────────────────────────────
@app.get("/")
def serve(): return FileResponse(os.path.join(frontend_path,'index.html'))

# ── Auth ──────────────────────────────────────────────────────────────────────
@app.post("/api/auth/login")
def login(req:LoginRequest):
    user=query_one("SELECT * FROM users WHERE username=%s AND is_active=true",(req.username,))
    if not user or not bcrypt.checkpw(req.password.encode(),user["password_hash"].encode()):
        raise HTTPException(status_code=401,detail="Invalid credentials")
    execute("UPDATE users SET last_login=NOW() WHERE id=%s",(user["id"],))
    return {"token":create_token(user["id"],user["role"]),"user":{"id":user["id"],"username":user["username"],"role":user["role"],"first_name":user["first_name"],"last_name":user["last_name"]}}

@app.get("/api/auth/me")
def me(user=Depends(get_current_user)):
    return query_one("SELECT id,username,email,first_name,last_name,role FROM users WHERE id=%s",(user["id"],))

# ── Dashboard ─────────────────────────────────────────────────────────────────
@app.get("/api/dashboard")
def dashboard(user=Depends(get_current_user)):
    stats={
        "vehicles_total": query_one("SELECT COUNT(*) as c FROM vehicles WHERE is_active=true")["c"],
        "drivers_total": query_one("SELECT COUNT(*) as c FROM drivers WHERE is_active=true")["c"],
        "fuel_cards_total": query_one("SELECT COUNT(*) as c FROM fuel_cards WHERE is_active=true")["c"],
        "projects_active": query_one("SELECT COUNT(*) as c FROM projects WHERE is_active=true")["c"],
        "reminders_active": query_one("SELECT COUNT(*) as c FROM reminders WHERE status='active'")["c"],
        "reminders_critical": query_one("SELECT COUNT(*) as c FROM reminders WHERE status='active' AND priority='critical'")["c"],
        "fuel_spend_month": float(query_one("SELECT COALESCE(SUM(total_cost),0) as c FROM fuel_transactions WHERE transaction_type='purchase' AND DATE_TRUNC('month',transaction_date)=DATE_TRUNC('month',NOW())")["c"]),
        "maintenance_spend_month": float(query_one("SELECT COALESCE(SUM(total_cost),0) as c FROM maintenance_records WHERE DATE_TRUNC('month',service_date)=DATE_TRUNC('month',NOW())")["c"]),
        "trips_month": query_one("SELECT COUNT(*) as c FROM trips WHERE DATE_TRUNC('month',trip_date)=DATE_TRUNC('month',NOW())")["c"],
    }
    reminders=query("""
        SELECT r.*,v.unit_number,v.registration,d.first_name||' '||d.last_name AS driver_name
        FROM reminders r LEFT JOIN vehicles v ON v.id=r.vehicle_id LEFT JOIN drivers d ON d.id=r.driver_id
        WHERE r.status='active' ORDER BY CASE r.priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, r.due_date ASC NULLS LAST LIMIT 10
    """)
    recent_fuel=query("""
        SELECT ft.*,v.unit_number,v.registration,d.first_name||' '||d.last_name AS driver_name,
               fc.card_number,vn.name AS vendor_name,p.name AS project_name
        FROM fuel_transactions ft JOIN vehicles v ON v.id=ft.vehicle_id
        LEFT JOIN drivers d ON d.id=ft.driver_id LEFT JOIN fuel_cards fc ON fc.id=ft.fuel_card_id
        LEFT JOIN vendors vn ON vn.id=ft.vendor_id LEFT JOIN projects p ON p.id=ft.project_id
        WHERE ft.transaction_type='purchase'
        ORDER BY ft.transaction_date DESC LIMIT 8
    """)
    fuel_by_month=query("""
        SELECT TO_CHAR(DATE_TRUNC('month',transaction_date),'Mon YY') AS month,
               SUM(total_cost) AS total_cost, SUM(litres) AS total_litres
        FROM fuel_transactions WHERE transaction_type='purchase' AND transaction_date>=NOW()-INTERVAL '6 months'
        GROUP BY DATE_TRUNC('month',transaction_date) ORDER BY DATE_TRUNC('month',transaction_date)
    """)
    cost_by_vehicle=query("""
        SELECT v.unit_number, v.registration,
               COALESCE(SUM(ft.total_cost),0) AS fuel_cost,
               COALESCE((SELECT SUM(mr.total_cost) FROM maintenance_records mr WHERE mr.vehicle_id=v.id AND mr.service_date>=NOW()-INTERVAL '3 months'),0) AS maint_cost
        FROM vehicles v LEFT JOIN fuel_transactions ft ON ft.vehicle_id=v.id AND ft.transaction_type='purchase' AND ft.transaction_date>=NOW()-INTERVAL '3 months'
        WHERE v.is_active=true GROUP BY v.id,v.unit_number,v.registration ORDER BY fuel_cost DESC LIMIT 8
    """)
    return {"stats":stats,"reminders":reminders,"recent_fuel":recent_fuel,"fuel_by_month":fuel_by_month,"cost_by_vehicle":cost_by_vehicle}

# ── Vehicles ──────────────────────────────────────────────────────────────────
@app.get("/api/vehicles")
def get_vehicles(search:Optional[str]=None,user=Depends(get_current_user)):
    sql="""SELECT v.*,d.name AS department_name,ft.name AS fuel_type_name,vt.name AS vehicle_type_name,
           vg.name AS group_name,vn.name AS purchase_vendor_name
           FROM vehicles v LEFT JOIN departments d ON d.id=v.department_id
           LEFT JOIN fuel_types ft ON ft.id=v.fuel_type_id LEFT JOIN vehicle_types vt ON vt.id=v.vehicle_type_id
           LEFT JOIN vehicle_groups vg ON vg.id=v.group_id LEFT JOIN vendors vn ON vn.id=v.purchase_vendor_id
           WHERE v.is_active=true"""
    params=[]
    if search: sql+=" AND (v.unit_number ILIKE %s OR v.registration ILIKE %s OR v.make ILIKE %s OR v.model ILIKE %s)"; params+=[f"%{search}%"]*4
    return query(sql+" ORDER BY v.unit_number",params)

@app.get("/api/vehicles/{vid}")
def get_vehicle(vid:int,user=Depends(get_current_user)):
    v=query_one("""SELECT v.*,d.name AS department_name,ft.name AS fuel_type_name,vt.name AS vehicle_type_name
           FROM vehicles v LEFT JOIN departments d ON d.id=v.department_id
           LEFT JOIN fuel_types ft ON ft.id=v.fuel_type_id LEFT JOIN vehicle_types vt ON vt.id=v.vehicle_type_id
           WHERE v.id=%s""",(vid,))
    if not v: raise HTTPException(404,"Vehicle not found")
    # Total costs
    costs=query_one("""
        SELECT COALESCE(SUM(CASE WHEN ft.transaction_type='purchase' THEN ft.total_cost ELSE 0 END),0) AS total_fuel,
               COALESCE((SELECT SUM(mr.total_cost) FROM maintenance_records mr WHERE mr.vehicle_id=%s),0) AS total_maintenance,
               COALESCE((SELECT SUM(ir.cost) FROM insurance_records ir WHERE ir.vehicle_id=%s),0) AS total_insurance,
               COALESCE((SELECT SUM(rr.cost) FROM roadworthy_records rr WHERE rr.vehicle_id=%s),0) AS total_roadworthy
        FROM fuel_transactions ft WHERE ft.vehicle_id=%s
    """,(vid,vid,vid,vid))
    v["costs"]=costs
    return v

@app.post("/api/vehicles",status_code=201)
def create_vehicle(data:VehicleCreate,user=Depends(get_current_user)):
    row=execute("""INSERT INTO vehicles (unit_number,registration,vin,make,model,year,color,engine_number,
        vehicle_type_id,fuel_type_id,department_id,group_id,tank_capacity,current_odometer,
        purchase_date,purchase_cost,purchase_vendor_id,insurance_policy,insurance_vendor_id,
        insurance_expiry,insurance_cost,roadworthy_number,roadworthy_expiry,roadworthy_cost,notes,photo_url)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (data.unit_number,data.registration,data.vin,data.make,data.model,data.year,data.color,data.engine_number,
         data.vehicle_type_id,data.fuel_type_id,data.department_id,data.group_id,data.tank_capacity,data.current_odometer,
         data.purchase_date,data.purchase_cost,data.purchase_vendor_id,data.insurance_policy,data.insurance_vendor_id,
         data.insurance_expiry,data.insurance_cost,data.roadworthy_number,data.roadworthy_expiry,data.roadworthy_cost,data.notes,data.photo_url))
    _refresh_vehicle_reminders(row["id"])
    return {"id":row["id"],"message":"Vehicle created"}

@app.put("/api/vehicles/{vid}")
def update_vehicle(vid:int,data:VehicleCreate,user=Depends(get_current_user)):
    execute("""UPDATE vehicles SET unit_number=%s,registration=%s,vin=%s,make=%s,model=%s,year=%s,color=%s,
        engine_number=%s,vehicle_type_id=%s,fuel_type_id=%s,department_id=%s,group_id=%s,tank_capacity=%s,
        insurance_policy=%s,insurance_vendor_id=%s,insurance_expiry=%s,insurance_cost=%s,
        roadworthy_number=%s,roadworthy_expiry=%s,roadworthy_cost=%s,notes=%s,photo_url=%s,updated_at=NOW() WHERE id=%s""",
        (data.unit_number,data.registration,data.vin,data.make,data.model,data.year,data.color,data.engine_number,
         data.vehicle_type_id,data.fuel_type_id,data.department_id,data.group_id,data.tank_capacity,
         data.insurance_policy,data.insurance_vendor_id,data.insurance_expiry,data.insurance_cost,
         data.roadworthy_number,data.roadworthy_expiry,data.roadworthy_cost,data.notes,data.photo_url,vid))
    _refresh_vehicle_reminders(vid)
    return {"message":"Updated"}

@app.delete("/api/vehicles/{vid}")
def delete_vehicle(vid:int,user=Depends(get_current_user)):
    execute("UPDATE vehicles SET is_active=false WHERE id=%s",(vid,)); return {"message":"Deactivated"}

def _refresh_vehicle_reminders(vid):
    v=query_one("SELECT * FROM vehicles WHERE id=%s",(vid,))
    if not v: return
    execute("DELETE FROM reminders WHERE vehicle_id=%s AND reminder_type IN ('insurance','roadworthy')",(vid,))
    today=datetime.now().date()
    label=f"{v['unit_number']} - {v['registration']}"
    if v.get("insurance_expiry"):
        exp=v["insurance_expiry"]
        days=(exp-today).days if hasattr(exp,'days') else 999
        if hasattr(exp,'strftime'): days=(exp-today).days
        pri="critical" if days<0 else "high" if days<=30 else "medium"
        title=f"Insurance {'EXPIRED' if days<0 else f'expiring in {days} days'} — {label}"
        execute("INSERT INTO reminders (vehicle_id,reminder_type,title,due_date,priority) VALUES (%s,'insurance',%s,%s,%s)",(vid,title,exp,pri))
    if v.get("roadworthy_expiry"):
        exp=v["roadworthy_expiry"]
        if hasattr(exp,'strftime'): days=(exp-today).days
        else: days=999
        pri="critical" if days<0 else "high" if days<=30 else "medium"
        title=f"Roadworthy {'EXPIRED' if days<0 else f'expiring in {days} days'} — {label}"
        execute("INSERT INTO reminders (vehicle_id,reminder_type,title,due_date,priority) VALUES (%s,'roadworthy',%s,%s,%s)",(vid,title,exp,pri))

# ── Drivers ───────────────────────────────────────────────────────────────────
@app.get("/api/drivers")
def get_drivers(search:Optional[str]=None,user=Depends(get_current_user)):
    sql="""SELECT d.*,dep.name AS department_name FROM drivers d
           LEFT JOIN departments dep ON dep.id=d.department_id WHERE d.is_active=true"""
    params=[]
    if search: sql+=" AND (d.first_name ILIKE %s OR d.last_name ILIKE %s OR d.employee_number ILIKE %s)"; params+=[f"%{search}%"]*3
    return query(sql+" ORDER BY d.last_name,d.first_name",params)

@app.post("/api/drivers",status_code=201)
def create_driver(data:DriverCreate,user=Depends(get_current_user)):
    row=execute("""INSERT INTO drivers (employee_number,first_name,last_name,job_title,email,phone,
        department_id,licence_number,licence_expiry,licence_state,health_ref,health_expiry,hire_date,hourly_wage,category_id,service_type,notes,photo_url)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (data.employee_number,data.first_name,data.last_name,data.job_title,data.email,data.phone,
         data.department_id,data.licence_number,data.licence_expiry,data.licence_state,
         data.health_ref,data.health_expiry,data.hire_date,data.hourly_wage,data.category_id,data.service_type,data.notes,data.photo_url))
    _refresh_driver_reminders(row["id"])
    return {"id":row["id"],"message":"Driver created"}

@app.put("/api/drivers/{did}")
def update_driver(did:int,data:DriverCreate,user=Depends(get_current_user)):
    execute("""UPDATE drivers SET employee_number=%s,first_name=%s,last_name=%s,job_title=%s,email=%s,phone=%s,
        department_id=%s,licence_number=%s,licence_expiry=%s,licence_state=%s,health_ref=%s,health_expiry=%s,
        hire_date=%s,hourly_wage=%s,category_id=%s,service_type=%s,notes=%s,photo_url=%s,updated_at=NOW() WHERE id=%s""",
        (data.employee_number,data.first_name,data.last_name,data.job_title,data.email,data.phone,
         data.department_id,data.licence_number,data.licence_expiry,data.licence_state,
         data.health_ref,data.health_expiry,data.hire_date,data.hourly_wage,data.category_id,data.service_type,data.notes,data.photo_url,did))
    _refresh_driver_reminders(did)
    return {"message":"Updated"}

def _refresh_driver_reminders(did):
    d=query_one("SELECT * FROM drivers WHERE id=%s",(did,))
    if not d: return
    execute("DELETE FROM reminders WHERE driver_id=%s AND reminder_type IN ('licence','health')",(did,))
    today=datetime.now().date()
    name=f"{d['first_name']} {d['last_name']}"
    if d.get("licence_expiry"):
        exp=d["licence_expiry"]
        if hasattr(exp,'strftime'): days=(exp-today).days
        else: days=999
        pri="critical" if days<0 else "high" if days<=30 else "medium"
        execute("INSERT INTO reminders (driver_id,reminder_type,title,due_date,priority) VALUES (%s,'licence',%s,%s,%s)",
                (did,f"Driver licence {'EXPIRED' if days<0 else f'expiring in {days} days'} — {name}",exp,pri))
    if d.get("health_expiry"):
        exp=d["health_expiry"]
        if hasattr(exp,'strftime'): days=(exp-today).days
        else: days=999
        pri="critical" if days<0 else "high" if days<=30 else "medium"
        execute("INSERT INTO reminders (driver_id,reminder_type,title,due_date,priority) VALUES (%s,'health',%s,%s,%s)",
                (did,f"Health certificate {'EXPIRED' if days<0 else f'expiring in {days} days'} — {name}",exp,pri))

# ── Fuel Cards ────────────────────────────────────────────────────────────────
@app.get("/api/fuel-cards")
def get_fuel_cards(user=Depends(get_current_user)):
    return query("""SELECT fc.*,v.unit_number,v.registration,d.first_name||' '||d.last_name AS driver_name
        FROM fuel_cards fc LEFT JOIN vehicles v ON v.id=fc.vehicle_id
        LEFT JOIN drivers d ON d.id=fc.driver_id WHERE fc.is_active=true ORDER BY fc.card_number""")

@app.post("/api/fuel-cards",status_code=201)
def create_fuel_card(data:FuelCardCreate,user=Depends(get_current_user)):
    row=execute("INSERT INTO fuel_cards (card_number,card_type,vehicle_id,driver_id,current_balance,initial_balance,notes) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id",
        (data.card_number,data.card_type,data.vehicle_id,data.driver_id,data.current_balance,data.current_balance,data.notes))
    return {"id":row["id"],"message":"Card created"}

@app.put("/api/fuel-cards/{cid}")
def update_fuel_card(cid:int,data:FuelCardCreate,user=Depends(get_current_user)):
    execute("UPDATE fuel_cards SET card_number=%s,vehicle_id=%s,driver_id=%s,notes=%s,updated_at=NOW() WHERE id=%s",
        (data.card_number,data.vehicle_id,data.driver_id,data.notes,cid))
    return {"message":"Updated"}

class BalanceAdjust(BaseModel):
    amount: float
 
@app.put("/api/fuel-cards/{cid}/adjust-balance")
def adjust_balance(cid: int, data: BalanceAdjust, user=Depends(get_current_user)):
    execute("UPDATE fuel_cards SET current_balance = current_balance + %s, updated_at=NOW() WHERE id=%s",
            (data.amount, cid))
    card = query_one("SELECT * FROM fuel_cards WHERE id=%s", (cid,))
    if card:
        _check_card_balance(card)
    return {"message": "Balance adjusted", "new_balance": float(card.get("current_balance", 0)) if card else 0}
 
# Soft-delete fuel card
@app.delete("/api/fuel-cards/{cid}")
def delete_fuel_card(cid: int, user=Depends(get_current_user)):
    execute("UPDATE fuel_cards SET is_active=false WHERE id=%s", (cid,))
    return {"message": "Deactivated"}

# Recalculate balance from initial_balance + all transactions (fixes corrupted balances)
@app.post("/api/fuel-cards/{cid}/recalculate")
def recalculate_balance(cid: int, user=Depends(get_current_user)):
    card = query_one("SELECT * FROM fuel_cards WHERE id=%s", (cid,))
    if not card: raise HTTPException(404, "Card not found")
    # Get the initial balance (stored when card was first created)
    initial = float(card.get("initial_balance") or 0)
    # Sum all transaction effects
    txns = query("SELECT transaction_type, total_cost FROM fuel_transactions WHERE fuel_card_id=%s", (cid,))
    net = 0
    for t in txns:
        amt = float(t.get("total_cost") or 0)
        if t["transaction_type"] == "topup":
            net += amt
        elif t["transaction_type"] == "purchase":
            net -= amt
        elif t["transaction_type"] == "transfer":
            net -= amt  # transfers out
    # Also add transfers IN to this card
    transfers_in = query("SELECT total_cost FROM fuel_transactions WHERE transfer_to_card_id=%s AND transaction_type='transfer'", (cid,))
    for t in transfers_in:
        net += float(t.get("total_cost") or 0)
    new_balance = initial + net
    execute("UPDATE fuel_cards SET current_balance=%s, updated_at=NOW() WHERE id=%s", (new_balance, cid))
    return {"message": "Balance recalculated", "initial_balance": initial, "net_transactions": net, "new_balance": new_balance}

# ── Fuel Transactions ─────────────────────────────────────────────────────────
@app.get("/api/fuel-transactions")
def get_fuel_tx(vehicle_id:Optional[int]=None,date_from:Optional[str]=None,date_to:Optional[str]=None,
                project_id:Optional[int]=None,tx_type:Optional[str]=None,limit:int=100,user=Depends(get_current_user)):
    sql="""SELECT ft.*,v.unit_number,v.registration,
           d.first_name||' '||d.last_name AS driver_name,
           fc.card_number,tc.card_number AS transfer_to_card_number,
           vn.name AS vendor_name,p.name AS project_name,ft2.name AS fuel_type_name
           FROM fuel_transactions ft JOIN vehicles v ON v.id=ft.vehicle_id
           LEFT JOIN drivers d ON d.id=ft.driver_id LEFT JOIN fuel_cards fc ON fc.id=ft.fuel_card_id
           LEFT JOIN fuel_cards tc ON tc.id=ft.transfer_to_card_id
           LEFT JOIN vendors vn ON vn.id=ft.vendor_id LEFT JOIN projects p ON p.id=ft.project_id
           LEFT JOIN fuel_types ft2 ON ft2.id=ft.fuel_type_id WHERE 1=1"""
    params=[]
    if vehicle_id: sql+=" AND ft.vehicle_id=%s"; params.append(vehicle_id)
    if date_from: sql+=" AND ft.transaction_date>=%s"; params.append(date_from)
    if date_to: sql+=" AND ft.transaction_date<=%s"; params.append(date_to)
    if project_id: sql+=" AND ft.project_id=%s"; params.append(project_id)
    if tx_type: sql+=" AND ft.transaction_type=%s"; params.append(tx_type)
    sql+=" ORDER BY ft.transaction_date DESC LIMIT %s"; params.append(limit)
    return query(sql,params)

@app.post("/api/fuel-transactions",status_code=201)
def create_fuel_tx(data:FuelTxCreate,user=Depends(get_current_user)):
    row=execute("""INSERT INTO fuel_transactions (transaction_date,transaction_type,vehicle_id,driver_id,
        fuel_card_id,transfer_to_card_id,fuel_type_id,vendor_id,project_id,location,trip_purpose,
        odometer_start,odometer_end,litres,cost_per_litre,total_cost,invoice_number,reference,is_full_tank,created_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (data.transaction_date,data.transaction_type,data.vehicle_id,data.driver_id,
         data.fuel_card_id,data.transfer_to_card_id,data.fuel_type_id,data.vendor_id,
         data.project_id,data.location,data.trip_purpose,data.odometer_start,data.odometer_end,
         data.litres,data.cost_per_litre,data.total_cost,data.invoice_number,data.reference,
         data.is_full_tank,f"user_{user['id']}"))
    if data.odometer_end and data.vehicle_id:
        execute("UPDATE vehicles SET current_odometer=%s,updated_at=NOW() WHERE id=%s AND current_odometer<%s",
                (data.odometer_end,data.vehicle_id,data.odometer_end))
    # ── Card balance logic (accounting rules) ──
    if data.transaction_type == "purchase" and data.fuel_card_id and data.total_cost:
        # PURCHASE: Deduct from card → this IS an expense
        execute("UPDATE fuel_cards SET current_balance = current_balance - %s, updated_at=NOW() WHERE id=%s",
                (data.total_cost, data.fuel_card_id))
        card = query_one("SELECT * FROM fuel_cards WHERE id=%s", (data.fuel_card_id,))
        if card: _check_card_balance(card)
    elif data.transaction_type == "transfer" and data.fuel_card_id and data.transfer_to_card_id and data.total_cost:
        # TRANSFER: Move cash from Card A to Card B → NOT an expense, just rebalancing
        # Deduct from source card
        execute("UPDATE fuel_cards SET current_balance = current_balance - %s, updated_at=NOW() WHERE id=%s",
                (data.total_cost, data.fuel_card_id))
        # Add to destination card
        execute("UPDATE fuel_cards SET current_balance = current_balance + %s, updated_at=NOW() WHERE id=%s",
                (data.total_cost, data.transfer_to_card_id))
        # Check both cards for low balance
        src = query_one("SELECT * FROM fuel_cards WHERE id=%s", (data.fuel_card_id,))
        if src: _check_card_balance(src)
        dst = query_one("SELECT * FROM fuel_cards WHERE id=%s", (data.transfer_to_card_id,))
        if dst: _check_card_balance(dst)
    return {"id":row["id"],"message":"Transaction recorded"}

@app.delete("/api/fuel-transactions/{tid}")
def delete_fuel_tx(tid:int,user=Depends(get_current_user)):
    # Reverse balance effect before deleting
    tx = query_one("SELECT * FROM fuel_transactions WHERE id=%s", (tid,))
    if tx and tx.get("total_cost"):
        amt = float(tx["total_cost"])
        if tx["transaction_type"] == "purchase" and tx.get("fuel_card_id"):
            # Purchase had deducted, so add back
            execute("UPDATE fuel_cards SET current_balance = current_balance + %s, updated_at=NOW() WHERE id=%s",
                    (amt, tx["fuel_card_id"]))
        elif tx["transaction_type"] == "topup" and tx.get("fuel_card_id"):
            # Topup had added, so subtract back
            execute("UPDATE fuel_cards SET current_balance = current_balance - %s, updated_at=NOW() WHERE id=%s",
                    (amt, tx["fuel_card_id"]))
        elif tx["transaction_type"] == "transfer":
            if tx.get("fuel_card_id"):
                # Transfer had deducted from source, add back
                execute("UPDATE fuel_cards SET current_balance = current_balance + %s, updated_at=NOW() WHERE id=%s",
                        (amt, tx["fuel_card_id"]))
            if tx.get("transfer_to_card_id"):
                # Transfer had added to dest, subtract back
                execute("UPDATE fuel_cards SET current_balance = current_balance - %s, updated_at=NOW() WHERE id=%s",
                        (amt, tx["transfer_to_card_id"]))
    execute("DELETE FROM fuel_transactions WHERE id=%s",(tid,))
    return {"message":"Deleted"}

# ── Trips ─────────────────────────────────────────────────────────────────────
@app.get("/api/trips")
def get_trips(vehicle_id:Optional[int]=None,driver_id:Optional[int]=None,
              project_id:Optional[int]=None,date_from:Optional[str]=None,date_to:Optional[str]=None,
              limit:int=100,user=Depends(get_current_user)):
    sql="""SELECT t.*,v.unit_number,v.registration,
           d.first_name||' '||d.last_name AS driver_name,p.name AS project_name,p.code AS project_code
           FROM trips t JOIN vehicles v ON v.id=t.vehicle_id
           LEFT JOIN drivers d ON d.id=t.driver_id LEFT JOIN projects p ON p.id=t.project_id WHERE 1=1"""
    params=[]
    if vehicle_id: sql+=" AND t.vehicle_id=%s"; params.append(vehicle_id)
    if driver_id: sql+=" AND t.driver_id=%s"; params.append(driver_id)
    if project_id: sql+=" AND t.project_id=%s"; params.append(project_id)
    if date_from: sql+=" AND t.trip_date>=%s"; params.append(date_from)
    if date_to: sql+=" AND t.trip_date<=%s"; params.append(date_to)
    sql+=" ORDER BY t.trip_date DESC,t.departure_time DESC LIMIT %s"; params.append(limit)
    return query(sql,params)

@app.post("/api/trips",status_code=201)
def create_trip(data:TripCreate,user=Depends(get_current_user)):
    row=execute("""INSERT INTO trips (vehicle_id,driver_id,project_id,trip_date,departure_time,return_time,
        origin,destination,purpose,odometer_start,odometer_end,passengers,notes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (data.vehicle_id,data.driver_id,data.project_id,data.trip_date,data.departure_time,
         data.return_time,data.origin,data.destination,data.purpose,data.odometer_start,
         data.odometer_end,data.passengers,data.notes))
    return {"id":row["id"],"message":"Trip logged"}

@app.delete("/api/trips/{tid}")
def delete_trip(tid:int,user=Depends(get_current_user)):
    execute("DELETE FROM trips WHERE id=%s",(tid,)); return {"message":"Deleted"}

# ── Maintenance ───────────────────────────────────────────────────────────────
@app.get("/api/maintenance")
def get_maintenance(vehicle_id:Optional[int]=None,limit:int=100,user=Depends(get_current_user)):
    sql="""SELECT mr.*,v.unit_number,v.registration,mt.name AS type_name,
           vn.name AS vendor_name,p.name AS project_name
           FROM maintenance_records mr JOIN vehicles v ON v.id=mr.vehicle_id
           LEFT JOIN maintenance_types mt ON mt.id=mr.maintenance_type_id
           LEFT JOIN vendors vn ON vn.id=mr.vendor_id LEFT JOIN projects p ON p.id=mr.project_id WHERE 1=1"""
    params=[]
    if vehicle_id: sql+=" AND mr.vehicle_id=%s"; params.append(vehicle_id)
    sql+=" ORDER BY mr.service_date DESC LIMIT %s"; params.append(limit)
    return query(sql,params)

@app.post("/api/maintenance",status_code=201)
def create_maintenance(data:MaintenanceCreate,user=Depends(get_current_user)):
    row=execute("""INSERT INTO maintenance_records (vehicle_id,maintenance_type_id,vendor_id,project_id,
        service_date,odometer,description,technician,labour_cost,parts_cost,total_cost,
        invoice_number,next_due_date,next_due_odometer,notes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (data.vehicle_id,data.maintenance_type_id,data.vendor_id,data.project_id,
         data.service_date,data.odometer,data.description,data.technician,
         data.labour_cost,data.parts_cost,data.total_cost,data.invoice_number,
         data.next_due_date,data.next_due_odometer,data.notes))
    if data.next_due_date and data.maintenance_type_id:
        execute("INSERT INTO reminders (vehicle_id,reminder_type,title,due_date,priority) VALUES (%s,'service',%s,%s,'medium') ON CONFLICT DO NOTHING",
                (data.vehicle_id,f"Service due — {data.description}",data.next_due_date))
    return {"id":row["id"],"message":"Record created"}

@app.put("/api/maintenance/{mid}")
def update_maintenance(mid:int,data:MaintenanceCreate,user=Depends(get_current_user)):
    execute("""UPDATE maintenance_records SET maintenance_type_id=%s,vendor_id=%s,project_id=%s,
        service_date=%s,odometer=%s,description=%s,technician=%s,labour_cost=%s,parts_cost=%s,
        total_cost=%s,invoice_number=%s,next_due_date=%s,next_due_odometer=%s,notes=%s,updated_at=NOW() WHERE id=%s""",
        (data.maintenance_type_id,data.vendor_id,data.project_id,data.service_date,data.odometer,
         data.description,data.technician,data.labour_cost,data.parts_cost,data.total_cost,
         data.invoice_number,data.next_due_date,data.next_due_odometer,data.notes,mid))
    return {"message":"Updated"}

# ── Insurance ─────────────────────────────────────────────────────────────────
@app.get("/api/insurance")
def get_insurance(vehicle_id:Optional[int]=None,user=Depends(get_current_user)):
    sql="""SELECT ir.*,v.unit_number,v.registration,vn.name AS vendor_name,p.name AS project_name
           FROM insurance_records ir JOIN vehicles v ON v.id=ir.vehicle_id
           LEFT JOIN vendors vn ON vn.id=ir.vendor_id LEFT JOIN projects p ON p.id=ir.project_id WHERE 1=1"""
    params=[]
    if vehicle_id: sql+=" AND ir.vehicle_id=%s"; params.append(vehicle_id)
    return query(sql+" ORDER BY ir.expiry_date DESC",params)

@app.post("/api/insurance",status_code=201)
def create_insurance(data:InsuranceCreate,user=Depends(get_current_user)):
    row=execute("""INSERT INTO insurance_records (vehicle_id,vendor_id,project_id,policy_number,start_date,expiry_date,cost,notes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (data.vehicle_id,data.vendor_id,data.project_id,data.policy_number,data.start_date,data.expiry_date,data.cost,data.notes))
    execute("UPDATE vehicles SET insurance_expiry=%s,insurance_cost=%s WHERE id=%s",(data.expiry_date,data.cost,data.vehicle_id))
    _refresh_vehicle_reminders(data.vehicle_id)
    return {"id":row["id"],"message":"Insurance record created"}

# ── Roadworthy ────────────────────────────────────────────────────────────────
@app.get("/api/roadworthy")
def get_roadworthy(vehicle_id:Optional[int]=None,user=Depends(get_current_user)):
    sql="""SELECT rr.*,v.unit_number,v.registration,vn.name AS vendor_name,p.name AS project_name
           FROM roadworthy_records rr JOIN vehicles v ON v.id=rr.vehicle_id
           LEFT JOIN vendors vn ON vn.id=rr.vendor_id LEFT JOIN projects p ON p.id=rr.project_id WHERE 1=1"""
    params=[]
    if vehicle_id: sql+=" AND rr.vehicle_id=%s"; params.append(vehicle_id)
    return query(sql+" ORDER BY rr.expiry_date DESC",params)

@app.post("/api/roadworthy",status_code=201)
def create_roadworthy(data:RoadworthyCreate,user=Depends(get_current_user)):
    row=execute("""INSERT INTO roadworthy_records (vehicle_id,vendor_id,project_id,certificate_number,issue_date,expiry_date,cost,notes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (data.vehicle_id,data.vendor_id,data.project_id,data.certificate_number,data.issue_date,data.expiry_date,data.cost,data.notes))
    execute("UPDATE vehicles SET roadworthy_expiry=%s,roadworthy_cost=%s WHERE id=%s",(data.expiry_date,data.cost,data.vehicle_id))
    _refresh_vehicle_reminders(data.vehicle_id)
    return {"id":row["id"],"message":"Roadworthy record created"}

# ── Reminders ─────────────────────────────────────────────────────────────────
@app.get("/api/reminders")
def get_reminders(status:Optional[str]=None,user=Depends(get_current_user)):
    sql="""SELECT r.*,v.unit_number,v.registration,v.make,v.model,v.department_id,
           dep.name AS department_name,d.first_name||' '||d.last_name AS driver_name
           FROM reminders r LEFT JOIN vehicles v ON v.id=r.vehicle_id
           LEFT JOIN departments dep ON dep.id=v.department_id
           LEFT JOIN drivers d ON d.id=r.driver_id"""
    params=[]
    if status: sql+=" WHERE r.status=%s"; params.append(status)
    sql+=" ORDER BY CASE r.priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, r.due_date ASC NULLS LAST"
    return query(sql,params)

@app.put("/api/reminders/{rid}")
def update_reminder(rid:int,data:ReminderUpdate,user=Depends(get_current_user)):
    if data.status=="acknowledged": execute("UPDATE reminders SET status='acknowledged',acknowledged_at=NOW() WHERE id=%s",(rid,))
    elif data.status=="resolved": execute("UPDATE reminders SET status='resolved',resolved_at=NOW() WHERE id=%s",(rid,))
    return {"message":"Updated"}

# ── Vendors ───────────────────────────────────────────────────────────────────
@app.get("/api/vendors")
def get_vendors(category:Optional[str]=None,user=Depends(get_current_user)):
    sql="SELECT * FROM vendors WHERE is_active=true"
    params=[]
    if category: sql+=" AND category=%s"; params.append(category)
    return query(sql+" ORDER BY name",params)

@app.post("/api/vendors",status_code=201)
def create_vendor(data:VendorCreate,user=Depends(get_current_user)):
    row=execute("INSERT INTO vendors (name,contact_person,phone,email,address,category,notes) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id",
        (data.name,data.contact_person,data.phone,data.email,data.address,data.category,data.notes))
    return {"id":row["id"],"message":"Vendor created"}

@app.put("/api/vendors/{vid}")
def update_vendor(vid:int,data:VendorCreate,user=Depends(get_current_user)):
    execute("UPDATE vendors SET name=%s,contact_person=%s,phone=%s,email=%s,address=%s,category=%s,notes=%s,updated_at=NOW() WHERE id=%s",
        (data.name,data.contact_person,data.phone,data.email,data.address,data.category,data.notes,vid))
    return {"message":"Updated"}

@app.delete("/api/vendors/{vid}")
def delete_vendor(vid:int,user=Depends(get_current_user)):
    execute("UPDATE vendors SET is_active=false WHERE id=%s",(vid,)); return {"message":"Deactivated"}

# ── Projects ──────────────────────────────────────────────────────────────────
@app.get("/api/projects")
def get_projects(user=Depends(get_current_user)):
    return query("SELECT * FROM projects ORDER BY is_active DESC,name")

@app.post("/api/projects",status_code=201)
def create_project(data:ProjectCreate,user=Depends(get_current_user)):
    row=execute("INSERT INTO projects (code,name,description,start_date,end_date) VALUES (%s,%s,%s,%s,%s) RETURNING id",
        (data.code,data.name,data.description,data.start_date,data.end_date))
    return {"id":row["id"],"message":"Project created"}

@app.put("/api/projects/{pid}")
def update_project(pid:int,data:ProjectCreate,user=Depends(get_current_user)):
    execute("UPDATE projects SET code=%s,name=%s,description=%s,start_date=%s,end_date=%s WHERE id=%s",
        (data.code,data.name,data.description,data.start_date,data.end_date,pid))
    return {"message":"Updated"}

# ── Users ─────────────────────────────────────────────────────────────────────
@app.get("/api/users")
def get_users(user=Depends(require_admin)):
    return query("SELECT id,username,email,first_name,last_name,role,is_active,last_login,created_at FROM users ORDER BY first_name")

@app.post("/api/users",status_code=201)
def create_user(data:UserCreate,user=Depends(require_admin)):
    pw=bcrypt.hashpw(data.password.encode(),bcrypt.gensalt()).decode()
    row=execute("INSERT INTO users (username,email,password_hash,first_name,last_name,role) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
        (data.username,data.email,pw,data.first_name,data.last_name,data.role))
    return {"id":row["id"],"message":"User created"}

@app.put("/api/users/{uid}/toggle")
def toggle_user(uid:int,user=Depends(require_admin)):
    execute("UPDATE users SET is_active=NOT is_active WHERE id=%s",(uid,)); return {"message":"Toggled"}

@app.put("/api/users/{uid}/password")
def change_password(uid:int,data:PasswordChange,user=Depends(require_admin)):
    if not data.password or len(data.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    pw=bcrypt.hashpw(data.password.encode(),bcrypt.gensalt()).decode()
    execute("UPDATE users SET password_hash=%s WHERE id=%s",(pw,uid))
    return {"message":"Password updated"}



# ── Photo Upload (base64) ─────────────────────────────────────────────────────
from fastapi import File, UploadFile
import base64

@app.post("/api/vehicles/{vid}/photo")
async def upload_vehicle_photo(vid:int, file:UploadFile=File(...), user=Depends(get_current_user)):
    contents = await file.read()
    if len(contents) > 2_000_000:
        raise HTTPException(400, "Photo must be under 2MB")
    b64 = f"data:{file.content_type};base64," + base64.b64encode(contents).decode()
    execute("UPDATE vehicles SET photo_url=%s, updated_at=NOW() WHERE id=%s", (b64, vid))
    return {"message": "Photo uploaded", "photo_url": b64}

@app.post("/api/drivers/{did}/photo")
async def upload_driver_photo(did:int, file:UploadFile=File(...), user=Depends(get_current_user)):
    contents = await file.read()
    if len(contents) > 2_000_000:
        raise HTTPException(400, "Photo must be under 2MB")
    b64 = f"data:{file.content_type};base64," + base64.b64encode(contents).decode()
    execute("UPDATE drivers SET photo_url=%s, updated_at=NOW() WHERE id=%s", (b64, did))
    return {"message": "Photo uploaded", "photo_url": b64}

# ── Lookups ───────────────────────────────────────────────────────────────────
@app.get("/api/lookups")
def get_lookups(user=Depends(get_current_user)):
    return {
        "fuel_types": query("SELECT * FROM fuel_types ORDER BY name"),
        "departments": query("SELECT * FROM departments ORDER BY name"),
        "vehicle_types": query("SELECT * FROM vehicle_types ORDER BY name"),
        "vehicle_groups": query("SELECT * FROM vehicle_groups ORDER BY name"),
        "maintenance_types": query("SELECT * FROM maintenance_types WHERE is_active=true ORDER BY name"),
        "vendors": query("SELECT id,name,category FROM vendors WHERE is_active=true ORDER BY name"),
        "projects": query("SELECT id,code,name FROM projects WHERE is_active=true ORDER BY name"),
        "fuel_cards": query("SELECT fc.id,fc.card_number,fc.card_type,v.unit_number FROM fuel_cards fc LEFT JOIN vehicles v ON v.id=fc.vehicle_id WHERE fc.is_active=true ORDER BY fc.card_number"),
        "drivers": query("SELECT id,employee_number,first_name,last_name FROM drivers WHERE is_active=true ORDER BY last_name"),
        "vehicles": query("SELECT id,unit_number,registration,make,model,photo_url FROM vehicles WHERE is_active=true ORDER BY unit_number"),
        "driver_categories": query("SELECT * FROM driver_categories ORDER BY name"),
        "service_types": query("SELECT * FROM service_types ORDER BY name"),
    }

# ── Reports ───────────────────────────────────────────────────────────────────
@app.get("/api/reports/vehicles")
def report_vehicles(user=Depends(get_current_user)):
    return query("""
        SELECT v.unit_number,v.registration,v.make,v.model,v.year,
               d.name AS department,vg.name AS grp,
               v.insurance_expiry,v.roadworthy_expiry,v.current_odometer,
               COALESCE(SUM(CASE WHEN ft.transaction_type='purchase' THEN ft.total_cost ELSE 0 END),0) AS total_fuel_cost,
               COALESCE((SELECT SUM(mr.total_cost) FROM maintenance_records mr WHERE mr.vehicle_id=v.id),0) AS total_maint_cost,
               COALESCE(v.insurance_cost,0) AS insurance_cost,
               COALESCE(v.roadworthy_cost,0) AS roadworthy_cost,
               COALESCE(SUM(CASE WHEN ft.transaction_type='purchase' THEN ft.total_cost ELSE 0 END),0)+
               COALESCE((SELECT SUM(mr.total_cost) FROM maintenance_records mr WHERE mr.vehicle_id=v.id),0)+
               COALESCE(v.insurance_cost,0)+COALESCE(v.roadworthy_cost,0) AS total_cost
        FROM vehicles v LEFT JOIN departments d ON d.id=v.department_id
        LEFT JOIN vehicle_groups vg ON vg.id=v.group_id
        LEFT JOIN fuel_transactions ft ON ft.vehicle_id=v.id
        WHERE v.is_active=true GROUP BY v.id,d.name,vg.name ORDER BY total_cost DESC
    """)

@app.get("/api/reports/fuel")
def report_fuel(date_from:Optional[str]=None,date_to:Optional[str]=None,
                vehicle_id:Optional[int]=None,project_id:Optional[int]=None,user=Depends(get_current_user)):
    sql="""SELECT ft.transaction_date,v.unit_number,v.registration,
           d.first_name||' '||d.last_name AS driver,vn.name AS station,
           ft.location,ft2.name AS fuel_type,ft.litres,ft.cost_per_litre,ft.total_cost,
           ft.odometer_start,ft.odometer_end,
           ft.reference,p.name AS project,fc.card_number
           FROM fuel_transactions ft JOIN vehicles v ON v.id=ft.vehicle_id
           LEFT JOIN drivers d ON d.id=ft.driver_id LEFT JOIN vendors vn ON vn.id=ft.vendor_id
           LEFT JOIN fuel_types ft2 ON ft2.id=ft.fuel_type_id
           LEFT JOIN projects p ON p.id=ft.project_id LEFT JOIN fuel_cards fc ON fc.id=ft.fuel_card_id
           WHERE ft.transaction_type='purchase'"""
    params=[]
    if date_from: sql+=" AND ft.transaction_date>=%s"; params.append(date_from)
    if date_to: sql+=" AND ft.transaction_date<=%s"; params.append(date_to)
    if vehicle_id: sql+=" AND ft.vehicle_id=%s"; params.append(vehicle_id)
    if project_id: sql+=" AND ft.project_id=%s"; params.append(project_id)
    return query(sql+" ORDER BY v.registration,v.unit_number,ft.transaction_date",params)

@app.get("/api/reports/personnel")
def report_personnel(user=Depends(get_current_user)):
    return query("""
        SELECT d.employee_number,d.first_name,d.last_name,d.job_title,dep.name AS department,
               d.phone,d.licence_expiry,d.health_expiry,
               COUNT(DISTINCT t.id) AS total_trips,
               COALESCE(SUM(t.distance),0) AS total_km
        FROM drivers d LEFT JOIN departments dep ON dep.id=d.department_id
        LEFT JOIN trips t ON t.driver_id=d.id
        LEFT JOIN fuel_transactions ft ON ft.driver_id=d.id AND ft.transaction_type='purchase'
        WHERE d.is_active=true GROUP BY d.id,dep.name ORDER BY d.last_name
    """)

@app.get("/api/reports/vendors")
def report_vendors(user=Depends(get_current_user)):
    return query("""
        SELECT vn.name,vn.category,vn.phone,vn.address,
               COALESCE(SUM(ft.total_cost),0) AS fuel_spend,
               COALESCE((SELECT SUM(mr.total_cost) FROM maintenance_records mr WHERE mr.vendor_id=vn.id),0) AS maint_spend,
               COALESCE(SUM(ft.total_cost),0)+COALESCE((SELECT SUM(mr.total_cost) FROM maintenance_records mr WHERE mr.vendor_id=vn.id),0) AS total_spend
        FROM vendors vn LEFT JOIN fuel_transactions ft ON ft.vendor_id=vn.id
        WHERE vn.is_active=true GROUP BY vn.id ORDER BY total_spend DESC
    """)

@app.get("/api/reports/project-costs")
def report_projects(user=Depends(get_current_user)):
    return query("""
        SELECT p.code,p.name,
               COALESCE(SUM(CASE WHEN ft.transaction_type='purchase' THEN ft.total_cost ELSE 0 END),0) AS fuel_cost,
               COALESCE((SELECT SUM(mr.total_cost) FROM maintenance_records mr WHERE mr.project_id=p.id),0) AS maint_cost,
               COUNT(DISTINCT ft.vehicle_id) AS vehicles_used,
               COUNT(DISTINCT t.id) AS trips
        FROM projects p
        LEFT JOIN fuel_transactions ft ON ft.project_id=p.id
        LEFT JOIN trips t ON t.project_id=p.id
        GROUP BY p.id ORDER BY fuel_cost DESC
    """)

# ── Settings ──────────────────────────────────────────────────────────────────
@app.get("/api/settings")
def get_settings(user=Depends(get_current_user)):
    rows = query("SELECT setting_key, setting_value, description FROM reminder_settings ORDER BY setting_key")
    return {r["setting_key"]: {"value": r["setting_value"], "description": r["description"]} for r in rows}

class SettingUpdate(BaseModel): value: str

@app.put("/api/settings/{key}")
def update_setting(key: str, data: SettingUpdate, user=Depends(get_current_user)):
    execute("UPDATE reminder_settings SET setting_value=%s, updated_at=NOW() WHERE setting_key=%s", (data.value, key))
    return {"message": "Updated"}


# ── Lookup Management (Settings) ──────────────────────────────────────────────
class LookupCreate(BaseModel):
    name: str

@app.get("/api/driver-categories")
def get_driver_categories(user=Depends(get_current_user)):
    return query("SELECT * FROM driver_categories ORDER BY name")

@app.post("/api/driver-categories", status_code=201)
def create_driver_category(data: LookupCreate, user=Depends(get_current_user)):
    row = execute("INSERT INTO driver_categories (name) VALUES (%s) RETURNING id", (data.name,))
    return {"id": row["id"], "message": "Created"}

@app.delete("/api/driver-categories/{cid}")
def delete_driver_category(cid: int, user=Depends(get_current_user)):
    execute("DELETE FROM driver_categories WHERE id=%s", (cid,))
    return {"message": "Deleted"}

@app.get("/api/service-types")
def get_service_types(user=Depends(get_current_user)):
    return query("SELECT * FROM service_types ORDER BY name")

@app.post("/api/service-types", status_code=201)
def create_service_type(data: LookupCreate, user=Depends(get_current_user)):
    row = execute("INSERT INTO service_types (name) VALUES (%s) RETURNING id", (data.name,))
    return {"id": row["id"], "message": "Created"}

@app.delete("/api/service-types/{sid}")
def delete_service_type(sid: int, user=Depends(get_current_user)):
    execute("DELETE FROM service_types WHERE id=%s", (sid,))
    return {"message": "Deleted"}

# ── Fuel Card Balance ─────────────────────────────────────────────────────────
class CardTopup(BaseModel):
    amount: float
    reference: Optional[str] = None
    topup_date: Optional[str] = None

class CardThreshold(BaseModel):
    balance_threshold: float

@app.post("/api/fuel-cards/{cid}/topup")
def topup_card(cid: int, data: CardTopup, user=Depends(get_current_user)):
    execute("UPDATE fuel_cards SET current_balance = current_balance + %s, updated_at=NOW() WHERE id=%s",
            (data.amount, cid))
    # Log as transaction
    dt = data.topup_date or datetime.now().isoformat()
    execute("""INSERT INTO fuel_transactions (transaction_date, transaction_type, fuel_card_id, total_cost, litres, reference, created_by)
               VALUES (%s, 'topup', %s, %s, 1, %s, %s)""",
            (dt, cid, data.amount, data.reference or f"Top-up GH₵{data.amount}", f"user_{user['id']}"))
    # Check threshold and create reminder if needed
    card = query_one("SELECT * FROM fuel_cards WHERE id=%s", (cid,))
    _check_card_balance(card)
    return {"message": "Card topped up"}

@app.put("/api/fuel-cards/{cid}/threshold")
def set_threshold(cid: int, data: CardThreshold, user=Depends(get_current_user)):
    execute("UPDATE fuel_cards SET balance_threshold=%s WHERE id=%s", (data.balance_threshold, cid))
    return {"message": "Threshold updated"}

def _check_card_balance(card):
    if not card: return
    bal = float(card.get("current_balance") or 0)
    threshold = float(card.get("balance_threshold") or 500)
    if bal <= threshold:
        execute("DELETE FROM reminders WHERE reference=%s AND reminder_type='fuel_card'", (f"card_{card['id']}",))
        pri = "critical" if bal <= 0 else "high" if bal <= threshold * 0.5 else "medium"
        execute("""INSERT INTO reminders (reminder_type, title, priority, reference)
                   VALUES ('fuel_card', %s, %s, %s)""",
                (f"Low balance on card {card['card_number']} — GH₵{bal:.2f} remaining", pri, f"card_{card['id']}"))

@app.get("/api/fuel-cards/{cid}/statement")
def card_statement(cid: int, user=Depends(get_current_user)):
    card = query_one("""SELECT fc.*, v.unit_number, v.registration 
                        FROM fuel_cards fc LEFT JOIN vehicles v ON v.id=fc.vehicle_id WHERE fc.id=%s""", (cid,))
    # Get transactions where this card is the source (fuel_card_id) OR the destination (transfer_to_card_id)
    txns = query("""SELECT ft.*, v.unit_number, v.registration,
                    d.first_name||' '||d.last_name AS driver_name,
                    vn.name AS vendor_name, p.name AS project_name,
                    fc_from.card_number AS from_card_number,
                    fc_to.card_number AS to_card_number,
                    CASE 
                        WHEN ft.transaction_type='transfer' AND ft.transfer_to_card_id=%s THEN 'transfer_in'
                        WHEN ft.transaction_type='transfer' AND ft.fuel_card_id=%s THEN 'transfer_out'
                        ELSE ft.transaction_type 
                    END AS display_type
                    FROM fuel_transactions ft 
                    LEFT JOIN vehicles v ON v.id=ft.vehicle_id
                    LEFT JOIN drivers d ON d.id=ft.driver_id
                    LEFT JOIN vendors vn ON vn.id=ft.vendor_id
                    LEFT JOIN projects p ON p.id=ft.project_id
                    LEFT JOIN fuel_cards fc_from ON fc_from.id=ft.fuel_card_id
                    LEFT JOIN fuel_cards fc_to ON fc_to.id=ft.transfer_to_card_id
                    WHERE ft.fuel_card_id=%s OR ft.transfer_to_card_id=%s
                    ORDER BY ft.transaction_date, ft.id""", (cid, cid, cid, cid))
    topups = sum(float(t["total_cost"] or 0) for t in txns if t["transaction_type"] == "topup")
    expenses = sum(float(t["total_cost"] or 0) for t in txns if t["transaction_type"] == "purchase")
    return {"card": card, "transactions": txns, "summary": {"topups": topups, "expenses": expenses, "balance": float(card.get("current_balance") or 0), "initial_balance": float(card.get("initial_balance") or 0)}}

@app.get("/api/reports/fuel-cards")
def report_fuel_cards(user=Depends(get_current_user)):
    cards = query("""SELECT fc.*, v.unit_number, v.registration, v.make, v.model,
                     COALESCE((SELECT SUM(total_cost) FROM fuel_transactions WHERE fuel_card_id=fc.id AND transaction_type='topup'),0) AS total_topups,
                     COALESCE((SELECT SUM(total_cost) FROM fuel_transactions WHERE fuel_card_id=fc.id AND transaction_type='purchase'),0) AS total_expenses,
                     COALESCE((SELECT SUM(total_cost) FROM fuel_transactions WHERE fuel_card_id=fc.id AND transaction_type='transfer'),0) AS total_transfers_out,
                     COALESCE((SELECT SUM(total_cost) FROM fuel_transactions WHERE transfer_to_card_id=fc.id AND transaction_type='transfer'),0) AS total_transfers_in,
                     (SELECT MAX(transaction_date) FROM fuel_transactions WHERE fuel_card_id=fc.id AND transaction_type='purchase') AS last_used
                     FROM fuel_cards fc LEFT JOIN vehicles v ON v.id=fc.vehicle_id
                     WHERE fc.is_active=true ORDER BY fc.card_number""")
    total_balance = sum(float(c.get("current_balance") or 0) for c in cards)
    total_topups = sum(float(c.get("total_topups") or 0) for c in cards)
    total_expenses = sum(float(c.get("total_expenses") or 0) for c in cards)
    return {"cards": cards, "summary": {"total_balance": total_balance, "total_topups": total_topups, "total_expenses": total_expenses}}
