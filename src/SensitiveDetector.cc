#include "SensitiveDetector.hh"

SensitiveDetector::SensitiveDetector(G4String name) : G4VSensitiveDetector(name){
    fTotalEnergyDeposited = 0.;
}

SensitiveDetector::~SensitiveDetector(){
}

void SensitiveDetector::Initialize(G4HCofThisEvent *){
    fTotalEnergyDeposited = 0.;
}

G4bool SensitiveDetector::ProcessHits(G4Step *aStep, G4TouchableHistory *){
    G4int eventID = G4RunManager::GetRunManager()->GetCurrentEvent()->GetEventID();

    G4AnalysisManager *analysisManager = G4AnalysisManager::Instance(); 

    G4StepPoint *preStepPoint = aStep->GetPreStepPoint();

    analysisManager->FillNtupleIColumn(0, 0, eventID);
    G4int detectorID = preStepPoint->GetTouchableHandle()->GetCopyNumber();
    analysisManager->FillNtupleIColumn(0, 1, detectorID);
    analysisManager->AddNtupleRow(0);

    G4double fEnergyDeposited = aStep->GetTotalEnergyDeposit();

    if (fEnergyDeposited>0){
        fTotalEnergyDeposited += fEnergyDeposited;
    }

    return true;
}

void SensitiveDetector::EndOfEvent(G4HCofThisEvent *){
    //G4cout << "Deposited energy: " << fTotalEnergyDeposited << G4endl;
    G4AnalysisManager *analysisManager = G4AnalysisManager::Instance();
}