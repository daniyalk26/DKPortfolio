
#include "ReservationSystem.hpp"
#include "Member.hpp"
#include "Officer.hpp"
#include "Coach.hpp"
#include <iostream>
#include <fstream>
#include <chrono>

using namespace std::chrono;

ReservationSystem::ReservationSystem(){
}

bool ReservationSystem::add_user(const std::shared_ptr<User>& u){
    return users_.emplace(u->username(),u).second;
}

std::shared_ptr<User> ReservationSystem::authenticate(const std::string& user,const std::string& pwd) const{
    auto it=users_.find(user);
    if(it!=users_.end() && it->second->check_password(pwd)) return it->second;
    return nullptr;
}

bool ReservationSystem::slot_available(int court,const TimeSlot& slot) const{
    for(const auto& r:reservations_){
        if(r.court()==court){
            auto start1=r.slot().start;
            auto end1=start1 + r.slot().duration;
            auto start2=slot.start;
            auto end2=start2 + slot.duration;
            if(!(end2<=start1 || start2>=end1)) return false;
        }
    }
    return true;
}

bool ReservationSystem::make_reservation(const std::shared_ptr<User>& u,int court,const TimeSlot& slot,bool open_play){
    if(court<1||court>3) return false;
    if(!slot_available(court,slot)) return false;
    Reservation res(court,slot,open_play);
    if(!u->can_make_reservation(res)) return false;
    if(!res.add_participant(u)) return false;
    reservations_.push_back(res);
    u->record_reservation(res);
    return true;
}

bool ReservationSystem::cancel_reservation(const std::shared_ptr<User>& u,int court,const TimeSlot& slot){
    for(auto it=reservations_.begin();it!=reservations_.end();++it){
        if(it->court()==court && it->slot().start==slot.start){
            bool allowed=false;
            if(u->type()==UserType::OFFICER) allowed=true;
            else {
                for(auto& wp:it->participants()){
                    if(auto sp=wp.lock(); sp && sp->username()==u->username()) {allowed=true; break;}
                }
            }
            if(!allowed) return false;
            for(auto& wp:it->participants()){
                if(auto sp=wp.lock()) sp->cancel_reservation(*it);
            }
            reservations_.erase(it);
            return true;
        }
    }
    return false;
}

void ReservationSystem::view_schedule(const sys_days& day) const{
    std::cout << "Schedule for "<< year_month_day{day} <<"\n";
    for(int c=1;c<=3;++c){
        std::cout << "Court "<<c<<":\n";
        for(const auto& r:reservations_){
            if(r.court()==c && floor<days>(r.slot().start)==day){
                auto tod=r.slot().start - day;
                int hr= duration_cast<hours>(tod).count();
                int mi= (duration_cast<minutes>(tod).count())%60;
                std::cout<< "  "<< (hr<10?"0":"") << hr <<":"<< (mi<10?"0":"")<<mi <<" - ";
                bool first=true;
                for(auto& wp:r.participants()){
                    if(auto sp=wp.lock()){
                        if(!first) std::cout<<", ";
                        std::cout<< sp->username();
                        first=false;
                    }
                }
                if(r.is_open_play()) std::cout << " (Open Play)";
                std::cout<<"\n";
            }
        }
    }
}

void ReservationSystem::save(const std::string& path) const{
    std::ofstream out(path);
    for(const auto& [name,u]:users_){
        out<<u->username()<<","<<static_cast<int>(u->type())<<"\n";
    }
}

void ReservationSystem::load(const std::string& path){
    // simple demo; not implemented
}
