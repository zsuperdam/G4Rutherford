#include "DetectorConstruction.hh"

DetectorConstruction::DetectorConstruction(){
}

DetectorConstruction::~DetectorConstruction(){
}

G4VPhysicalVolume *DetectorConstruction::Construct(){
    G4bool checkOverlaps = true;

    // environment

    G4NistManager *nist = G4NistManager::Instance();
    G4Material *worldMat = nist->FindOrBuildMaterial("G4_Galactic");
    G4Material *gold = nist->FindOrBuildMaterial("G4_Au");
    G4Material *silicon = nist->FindOrBuildMaterial("G4_Si");

    G4double xWorld = 10. * cm;
    G4double yWorld = 10. * cm;
    G4double zWorld = 10. * cm;

    G4Box *solidWorld = new G4Box("solidWorld", xWorld, yWorld, zWorld);
    G4LogicalVolume *logicWorld = new G4LogicalVolume(solidWorld, worldMat, "logicalWorld");
    G4VPhysicalVolume *physWorld = new G4PVPlacement(0, G4ThreeVector(0., 0., 0.), logicWorld, "physWorld", 0, false, 0, checkOverlaps);



    //gold
    G4double goldThickness = 3. * um;
    G4double goldSize = 2. * cm;
    G4Box *solidGold = new G4Box("solidGold", 0.5 * goldSize, 0.5 * goldSize, 0.5 * goldThickness);
    G4LogicalVolume *logicGold = new G4LogicalVolume(solidGold, gold, "logicalGold");
    G4VPhysicalVolume *physGold = new G4PVPlacement(0, G4ThreeVector(0., 0., 0.), logicGold, "physGold", logicWorld, false, checkOverlaps);

    G4VisAttributes *goldVisAtt = new G4VisAttributes(G4Color(1.0, 1.0, 0.0, 0.5));
    goldVisAtt->SetForceSolid(true);
    logicGold->SetVisAttributes(goldVisAtt);


    // Parametri dei rivelatori
    G4double detectorLenght = .15 * cm;
    G4double detectorWidth = 300. * um;
    G4Box *solidDetector = new G4Box("solidDetector", 0.5 * detectorLenght, 0.5 * detectorLenght, 0.5 * detectorWidth);
    logicDetector = new G4LogicalVolume(solidDetector, silicon, "logicDetector");

    // Visibilità
    G4VisAttributes *detVisAtt = new G4VisAttributes(G4Color(1.0, 1.0, 1.0, 0.5));
    detVisAtt->SetForceSolid(true);

    // Numero di rivelatori e configurazione della posizione
    G4int numDetectors = 95; // Numero di rivelatori
    G4double radius = 5.0 * cm; // Raggio da utilizzare per la posizione dei rivelatori
    G4double angleStep = 1.8 * deg; // Passo angolare (90° per posizionarli agli angoli)

    new G4PVPlacement(0, G4ThreeVector(0., 0., radius), logicDetector, "physDetector", logicWorld, false, 0, checkOverlaps);
    logicDetector->SetVisAttributes(detVisAtt);

    for(G4int i = 1; i < numDetectors + 1; i++) {
        G4double angle = i * angleStep; // Calcolo dell'angolo per ogni rivelatore

        // Calcolare la posizione
        G4ThreeVector position(radius * std::sin(angle), 0.0, radius * std::cos(angle));

        // Creazione del rivelatore
        G4RotationMatrix *rotation = new G4RotationMatrix();
        rotation->rotateY(-angle);
        new G4PVPlacement(rotation, position, logicDetector, "physDetector", logicWorld, false, i, checkOverlaps);
        logicDetector->SetVisAttributes(detVisAtt);

        G4ThreeVector position2(-radius * std::sin(angle), 0.0, radius * std::cos(angle));
        G4RotationMatrix *rotation2 = new G4RotationMatrix();
        rotation2->rotateY(angle);
        new G4PVPlacement(rotation2, position2, logicDetector, "physDetector", logicWorld, false, -i, checkOverlaps);
        logicDetector->SetVisAttributes(detVisAtt);
    }


    return physWorld;
}

void DetectorConstruction::ConstructSDandField(){
    SensitiveDetector *sensDet = new SensitiveDetector("SensitiveDetector");
    logicDetector->SetSensitiveDetector(sensDet);
    G4SDManager::GetSDMpointer()->AddNewDetector(sensDet);
}