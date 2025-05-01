
#pragma once
#include "User.hpp"
#include <map>
#include <chrono>

enum class Skill { A, B, C };
struct DayCounter {
    int minutes=0;
};
struct WeekKey {
    int year;
    int week;
    bool operator<(const WeekKey& o) const {
        return std::tie(year, week) < std::tie(o.year, o.week);
    }
};
struct WeekCounter {
    int minutes=0;
};

class Member : public User {
    Skill skill_;
    mutable std::map<WeekKey,WeekCounter> week_usage_;
    mutable std::map<std::chrono::sys_days,DayCounter> day_usage_;
public:
    Member(std::string username,std::string password,Skill s,UserType t=UserType::MEMBER)
        : User(std::move(username),std::move(password),t), skill_{s} {}
    Skill skill() const { return skill_; }
    bool can_make_reservation(const Reservation& res) const override;
    void record_reservation(const Reservation& res) override;
    void cancel_reservation(const Reservation& res) override;
};
