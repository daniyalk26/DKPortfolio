
#include "ReservationSystem.hpp"
#include "Member.hpp"
#include "Officer.hpp"
#include "Coach.hpp"
#include <iostream>
#include <chrono>
#include <iomanip>

using namespace std::chrono;

int main(){
    ReservationSystem sys;
    // seed users
    sys.add_user(std::make_shared<Member>("alice","pass",Skill::A));
    sys.add_user(std::make_shared<Member>("bob","pass",Skill::B));
    sys.add_user(std::make_shared<Officer>("olivia","pass",Skill::A));
    sys.add_user(std::make_shared<Coach>("coach_kim","pass"));
    std::cout << "Court Reservation System\n";
    std::string user,pwd;
    while(true){
        std::cout << "Username (or exit): "; std::cin>>user;
        if(user=="exit") break;
        std::cout << "Password: "; std::cin>>pwd;
        auto u=sys.authenticate(user,pwd);
        if(!u){ std::cout<<"Invalid login\n"; continue;}
        bool done=false;
        while(!done){
            std::cout<<"1.View schedule 2.Make reservation 3.Cancel reservation 4.Logout\n";
            int ch; std::cin>>ch;
            if(ch==1){
                auto today=floor<days>(system_clock::now());
                sys.view_schedule(today);
            }else if(ch==2){
                int court; int day_offset; int hour; int minute;
                std::cout<<"Court(1-3) DayOffset(0=today) Hour Minute: ";
                std::cin>>court>>day_offset>>hour>>minute;
                auto start=floor<days>(system_clock::now())+days{day_offset}+hours{hour}+minutes{minute};
                TimeSlot slot{start,minutes{30}};
                if(sys.make_reservation(u,court,slot)){
                    std::cout<<"Reserved!\n";
                }else std::cout<<"Failed\n";
            }else if(ch==3){
                int court; int day_offset; int hour; int minute;
                std::cout<<"Court DayOffset Hour Minute: ";
                std::cin>>court>>day_offset>>hour>>minute;
                auto start=floor<days>(system_clock::now())+days{day_offset}+hours{hour}+minutes{minute};
                TimeSlot slot{start,minutes{30}};
                if(sys.cancel_reservation(u,court,slot)) std::cout<<"Cancelled\n";
                else std::cout<<"Failed\n";
            }else done=true;
        }
    }
}
