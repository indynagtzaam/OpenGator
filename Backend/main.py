from fastapi import FastAPI
from anthropic import Anthropic 
from dotenv import load_dotenv
import os 
from pydantic import BaseModel
from supabase import create_client

app = FastAPI()
load_dotenv()
client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

FASE_PROMPTS = {
    1:"Geef een volledige, werkende oplossing met duidelijke uitleg.",
    2:"Geef een gedeeltelijke oplossing met hints. Laat de gebruiker het laatste stuk zelf invullen van wat hij net heeft geleerd.",
    3:"Geef geen code. Stel alleen een sturende vraag die de gebruiker naar het antwoord leidt.",
    4:"Geef geen hulp tenzij de gebruiker expliciet om de volledige oplossing vraagt "
}

CONCEPTEN_LIJST = [
    "variabelen",
    "loops",
    "functions",
    "dictionaries",
    "lists",
    "classes",
    "conditionals",
    "error handling",
    "string manipulatie",
    "list comprehension"
]

class VraagInput(BaseModel):
    vraag: str  

@app.post("/vraag")
def stel_vraag(input: VraagInput):
    concept_naam = classificeer_concept(input.vraag)
    concept_id = haal_of_maak_concept(concept_naam)
    fase = haal_of_maak_fase("indy", concept_id)


    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=FASE_PROMPTS[fase], 
        messages=[{"role": "user", "content": input.vraag}] 
)
    return {"Antwoord": response.content[0].text, "fase": fase, "concept": concept_naam}

def classificeer_concept(vraag: str ):
    lijst_tekst = ", ".join(CONCEPTEN_LIJST)
    aanroepen = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=50,
        system=f"Kies het concept uit deze exacte lijst dat het beste bij de vraag past: {lijst_tekst}. Antwoord met alleen de exacte naam uit de lijst, niets anders.", 
        messages= [{"role": "user", "content": vraag}]
    )
    return aanroepen.content[0].text

@app.post("/test-classificatie")
def test_classificatie(input: VraagInput):
    concept = classificeer_concept(input.vraag)
    return {"concept": concept}

def haal_of_maak_concept(conceptnaam: str):
    resultaat = supabase.table("concepten").select("*").eq("naam", conceptnaam).execute()

    if len(resultaat.data) > 0:
        return resultaat.data[0]["id"]
    else:
        nieuw = supabase.table("concepten").insert({"naam": conceptnaam}).execute()
        return nieuw.data[0]["id"]

@app.post("/test-concept")
def test_concept(input: VraagInput):
    concept_naam = classificeer_concept(input.vraag)
    concept_id = haal_of_maak_concept(concept_naam)
    return {"concept_naam": concept_naam, "concept_id": concept_id}

def haal_of_maak_fase(gebruiker_id: str, concept_id: str):
    resultaat = supabase.table("gebruikers_voortgang").select("*").eq("gebruiker_id", gebruiker_id).eq("concept_id", concept_id).execute()

    if len(resultaat.data) > 0:
        return resultaat.data[0]["fase"]
    else:
        nieuw = supabase.table("gebruikers_voortgang").insert({
        "gebruiker_id": gebruiker_id,
        "concept_id": concept_id,
        "fase": 1 
    }).execute()
        return nieuw.data[0]["fase"]

@app.post("/test-fase")
def test_fase(input: VraagInput):
    concept_naam = classificeer_concept(input.vraag)
    concept_id = haal_of_maak_concept(concept_naam)
    fase = haal_of_maak_fase("indy", concept_id)
    return {"concept_naam": concept_naam, "concept_id": concept_id, "fase": fase}