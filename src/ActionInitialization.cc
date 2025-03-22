#include "ActionInitialization.hh"

ActionInitialization::ActionInitialization(){
}

ActionInitialization::~ActionInitialization(){
}

void ActionInitialization::BuildForMaster() const{
}

void ActionInitialization::Build() const{
    PrimaryGenerator *generator = new PrimaryGenerator();
    SetUserAction(generator);
}