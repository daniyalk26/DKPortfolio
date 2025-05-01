
#pragma once
#include "User.hpp"
class Coach : public User {
public:
    Coach(std::string u,std::string p)
        : User(std::move(u),std::move(p),UserType::COACH){}
    bool can_make_reservation(const Reservation& res) const override;
    void record_reservation(const Reservation&) override {}
    void cancel_reservation(const Reservation&) override {}
};
