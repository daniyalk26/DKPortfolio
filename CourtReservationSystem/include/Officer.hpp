
#pragma once
#include "Member.hpp"
class Officer : public Member {
public:
    Officer(std::string u,std::string p,Skill s)
        : Member(std::move(u),std::move(p),s,UserType::OFFICER){}
    bool can_make_reservation(const Reservation& res) const override;
};
