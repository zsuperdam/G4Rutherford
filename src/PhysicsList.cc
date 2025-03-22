#include "PhysicsList.hh"

PhysicsList::PhysicsList(){
    //EM Physics
    RegisterPhysics(new G4EmStandardPhysics());
}

PhysicsList::~PhysicsList(){
}