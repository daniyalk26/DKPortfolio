
#pragma once
#include <vector>
#include <memory>
#include <unordered_map>
#include <string>
#include "Reservation.hpp"
#include "User.hpp"

class ReservationSystem {
    std::unordered_map<std::string,std::shared_ptr<User>> users_;
    std::vector<Reservation> reservations_;
public:
    ReservationSystem();
    bool add_user(const std::shared_ptr<User>& u);
    std::shared_ptr<User> authenticate(const std::string& user,const std::string& pwd) const;
    bool make_reservation(const std::shared_ptr<User>& u,int court,const TimeSlot& slot,bool open_play=false);
    bool cancel_reservation(const std::shared_ptr<User>& u,int court,const TimeSlot& slot);
    void view_schedule(const std::chrono::sys_days& day) const;
    void save(const std::string& path) const;
    void load(const std::string& path);
private:
    bool slot_available(int court,const TimeSlot& slot) const;
};
