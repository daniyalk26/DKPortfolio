
#pragma once
#include <string>
#include <vector>
#include <chrono>
#include <memory>

class User;
struct TimeSlot {
    std::chrono::sys_seconds start;
    std::chrono::minutes duration{30};
};

class Reservation {
    int court_id_;
    TimeSlot slot_;
    std::vector<std::weak_ptr<User>> participants_;
    bool open_play_=false;
public:
    Reservation(int court_id, TimeSlot slot,bool open=false)
        : court_id_{court_id},slot_{slot},open_play_{open}{}
    int court() const { return court_id_; }
    const TimeSlot& slot() const { return slot_; }
    bool is_open_play() const { return open_play_; }
    bool add_participant(const std::shared_ptr<User>& u);
    bool remove_participant(const std::string& username);
    const std::vector<std::weak_ptr<User>>& participants() const { return participants_; }
};
