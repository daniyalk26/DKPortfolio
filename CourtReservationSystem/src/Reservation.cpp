
#include "Reservation.hpp"
#include "User.hpp"
bool Reservation::add_participant(const std::shared_ptr<User>& u){
    for(auto& wp:participants_){
        if(auto sp=wp.lock();sp && sp->username()==u->username()) return false;
    }
    if(participants_.size()>=2 && !open_play_) return false;
    participants_.push_back(u);
    return true;
}
bool Reservation::remove_participant(const std::string& username){
    for(auto it=participants_.begin();it!=participants_.end();++it){
        if(auto sp=it->lock(); sp && sp->username()==username){
            participants_.erase(it);
            return true;
        }
    }
    return false;
}
