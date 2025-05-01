
#pragma once
#include <string>
#include <memory>
#include <vector>

class Reservation;
enum class UserType { MEMBER, OFFICER, COACH };

class User {
protected:
    std::string username_;
    std::string password_;
    UserType type_;
public:
    User(std::string username, std::string password, UserType t)
        : username_{std::move(username)}, password_{std::move(password)}, type_{t} {}
    virtual ~User() = default;
    const std::string& username() const { return username_; }
    bool check_password(const std::string& pwd) const { return pwd == password_; }
    UserType type() const { return type_; }
    virtual bool can_make_reservation(const Reservation& res) const = 0;
    virtual void record_reservation(const Reservation& res) = 0;
    virtual void cancel_reservation(const Reservation& res) = 0;
};
