#include "PrimaryGenerator.hh"

// custom energy (data taken from www.lnhb.fr/nuclides/Am-241_tables.pdf)
G4double CustomAm241Energy(){
    G4double randomNumber = G4UniformRand();

    // alpha 0,2
    if(randomNumber < 0.8445){
        return 5.57828 * MeV;
    }

    // alpha 0,4
    else if(randomNumber < 0.9768){
        return 5.53486 * MeV;
    }

    // alpha 0,6
    else if(randomNumber < 0.9934){
        return 5.47932 * MeV;
    }

    //alpha 0,0
    else if(randomNumber < 0.9972){
        return 5.63782 * MeV;
    }

    // alpha 0,1
    else if(randomNumber < 0.9995){ 
        return 5.60462 * MeV;
    }

    //there is ~0.0005 of probability of dfferent alpha particle energies, 
    // in the case the random generated number would be one of those t is 
    // re-genarated for code smplicity (it is actually wrong snce we are 
    // assuming no alpha particle with energy different from those stated 
    // before exists whereas there exists ~30 more)
    else{
        return 5.57828 * MeV;
    }
}

PrimaryGenerator::PrimaryGenerator(){
    fParticleGun = new G4ParticleGun(1);

    // Particle position
    G4double x = 0. * m;
    G4double y = 0. * m;
    G4double z = 0. * m;

    G4ThreeVector pos(x, y, z);

    // particle direction
    G4double px = 0.;
    G4double py = 0.;
    G4double pz = 1.;

    G4ThreeVector mom(px, py, pz);

    // particle type
    G4ParticleTable *particleTable = G4ParticleTable::GetParticleTable();
    G4ParticleDefinition *particle = particleTable->FindParticle("alpha");

    fParticleGun->SetParticlePosition(pos);
    fParticleGun->SetParticleMomentumDirection(mom);
    // fParticleGun->SetParticleEnergy(5.4 * MeV); // the energy is being assigned in the GeneratePrimaries function s.t. it is always different
    fParticleGun->SetParticleDefinition(particle);
}

PrimaryGenerator::~PrimaryGenerator(){
    delete fParticleGun;
}

void PrimaryGenerator::GeneratePrimaries(G4Event *anEvent){
    // Create vertex
    G4double energy = CustomAm241Energy();
    fParticleGun->SetParticleEnergy(energy);
    fParticleGun->GeneratePrimaryVertex(anEvent);
    G4cout << energy << G4endl;
}