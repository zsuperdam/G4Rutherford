#include "RunAction.hh"

RunAction::RunAction(){
    G4AnalysisManager *analysisManager = G4AnalysisManager::Instance();

    analysisManager->SetNtupleMerging(true); // merging of the multiple output created by each individual thread
    // need to have compiled G4 with root, if "geant4-config --has-feature ROOT" returns no then comment the previous line
    
    analysisManager->CreateNtuple("Events", "Events"); //creazione Ntuple
    analysisManager->CreateNtupleIColumn("Event");
    analysisManager->CreateNtupleIColumn("DetectorID"); //creazione colonna con Id del detector
    analysisManager->FinishNtuple(); //fine creazione Ntuple
}

RunAction::~RunAction(){
}

void RunAction::BeginOfRunAction(const G4Run *run){
    G4AnalysisManager *analysisManager = G4AnalysisManager::Instance();

    G4int runID = run->GetRunID();
    std::stringstream strRunID;
    strRunID << runID;
    analysisManager->OpenFile("output" + strRunID.str() + ".root");
}

void RunAction::EndOfRunAction(const G4Run *run){
    G4AnalysisManager *analysisManager = G4AnalysisManager::Instance();
    analysisManager->Write();
    analysisManager->CloseFile();
    G4int runID = run->GetRunID();
    G4cout << "Run " << runID << " ended" << G4endl;
}
