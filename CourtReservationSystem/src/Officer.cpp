
#include "Officer.hpp"
#include "Reservation.hpp"
bool Officer::can_make_reservation(const Reservation& res) const{
    // Officer inherits same limits for personal reservations.
    return Member::can_make_reservation(res);
}
