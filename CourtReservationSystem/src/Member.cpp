
#include "Member.hpp"
#include "Reservation.hpp"
#include <chrono>
#include <ctime>

using namespace std::chrono;

// Helper to get ISO week number and year from sys_days
WeekKey get_week_key(sys_days day) {
    std::time_t tt = system_clock::to_time_t(day);
    std::tm tm = *std::gmtime(&tt);

    char buf[10];
    std::strftime(buf, sizeof(buf), "%G-%V", &tm); // ISO year and week

    int year, week;
    sscanf(buf, "%d-%d", &year, &week);
    return WeekKey{year, week};
}

bool Member::can_make_reservation(const Reservation& res) const {
    if(res.is_open_play()) return true;
    auto day = floor<days>(res.slot().start);
    auto& dc = day_usage_[day];
    auto wk = get_week_key(day);
    auto& wc = week_usage_[wk];
    if(dc.minutes + res.slot().duration.count() > 30) return false;
    if(wc.minutes + res.slot().duration.count() > 60) return false;
    return true;
}

void Member::record_reservation(const Reservation& res) {
    if(res.is_open_play()) return;
    auto day = floor<days>(res.slot().start);
    day_usage_[day].minutes += res.slot().duration.count();
    auto wk = get_week_key(day);
    week_usage_[wk].minutes += res.slot().duration.count();
}

void Member::cancel_reservation(const Reservation& res) {
    if(res.is_open_play()) return;
    auto day = floor<days>(res.slot().start);
    day_usage_[day].minutes -= res.slot().duration.count();
    auto wk = get_week_key(day);
    week_usage_[wk].minutes -= res.slot().duration.count();
}
