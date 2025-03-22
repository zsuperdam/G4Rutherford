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

    G4double xWorld = 5. * cm;
    G4double yWorld = 5. * cm;
    G4double zWorld = 5. * cm;

    G4Box *solidWorld = new G4Box("solidWorld", xWorld, yWorld, zWorld);
    G4LogicalVolume *logicWorld = new G4LogicalVolume(solidWorld, worldMat, "logicalWorld");
    G4VPhysicalVolume *physWorld = new G4PVPlacement(0, G4ThreeVector(0., 0., 0.), logicWorld, "physWorld", 0, false, 0, checkOverlaps);



    //gold
    G4double goldThickness = 3. * um;
    G4double goldSize = 2. * cm;
    G4Box *solidGold = new G4Box("solidGold", 0.5 * goldSize, 0.5 * goldSize, 0.5 * goldThickness);
    G4LogicalVolume *logicGold = new G4LogicalVolume(solidGold, gold, "logicalGold");
    G4VPhysicalVolume *physGold = new G4PVPlacement(0, G4ThreeVector(0., 0., 1. * cm), logicGold, "physGold", logicWorld, false, checkOverlaps);

    G4VisAttributes *goldVisAtt = new G4VisAttributes(G4Color(1.0, 1.0, 0.0, 0.5));
    goldVisAtt->SetForceSolid(true);
    logicGold->SetVisAttributes(goldVisAtt);


    //detector
    G4double innerRadius = 3. * cm;
    G4double outerRadius = 3.005 * cm;
    G4double zLenght = 1 * mm;
    G4double startAngle = 0. * deg;
    G4double endAngle = 360. * deg;
    G4Tubs *solidDetector = new G4Tubs("solidDetector", innerRadius, outerRadius, 0.5 * zLenght, startAngle, endAngle);
    logicDetector = new G4LogicalVolume(solidDetector, silicon, "logicDetector");
    G4RotationMatrix* rotation = new G4RotationMatrix();
    rotation->rotateX(90.*deg);
    G4VPhysicalVolume *physDetector = new G4PVPlacement(rotation, G4ThreeVector(0, 0, 1. * cm), logicDetector, "physDetector", logicWorld, false, checkOverlaps);

    G4VisAttributes *detVisAtt = new G4VisAttributes(G4Color(1.0, 1.0, 1.0, 0.5));
    detVisAtt->SetForceSolid(true);
    logicDetector->SetVisAttributes(detVisAtt);
    
    return physWorld;
}

void DetectorConstruction::ConstructSDandField(){
    SensitiveDetector *sensDet = new SensitiveDetector("SensitiveDetector");
    logicDetector->SetSensitiveDetector(sensDet);
    G4SDManager::GetSDMpointer()->AddNewDetector(sensDet);
}