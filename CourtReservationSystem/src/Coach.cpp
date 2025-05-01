
#include "Coach.hpp"
#include "Reservation.hpp"
#include <chrono>

using namespace std::chrono;

bool within_coach_hours(const sys_seconds& tp){
    // weekday between Monday (1) to Friday (5)
    weekday wd=floor<days>(tp);
    if(wd==weekday{0}||wd==weekday{6}) return false;
    auto tod=tp - floor<days>(tp);
    auto minutes_since_midnight=duration_cast<minutes>(tod).count();
    // coaching windows: 9-12 and 15-18 -> 9*60=540 to 720, 900 to 1080
    return (minutes_since_midnight>=540 && minutes_since_midnight<720) ||
           (minutes_since_midnight>=900 && minutes_since_midnight<1080);
}

bool Coach::can_make_reservation(const Reservation& res) const{
    if(!within_coach_hours(res.slot().start)) return false;
    // advanced booking? (should be at least 48h if want priority; but we'll allow booking if slot free anyway)
    return true;
}
