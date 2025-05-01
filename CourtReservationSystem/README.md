# Court Reservation System 🏸

A command‑line tool (C++20) for managing court reservations at a sports club.  
Supports **members**, **coaches**, and **officers** with role‑based permissions.

## Features

| Role | Capabilities |
|------|--------------|
| Member | View available slots, book or cancel a reservation |
| Coach  | Reserve coaching courts, manage student lists |
| Officer| Override bookings, generate daily reports |

Data is persisted to plain‑text files for simplicity but can be swapped for a database layer.

## Build & run

### Prerequisites

* GCC ≥ 10 or Clang ≥ 12 (C++20 support)
* `make`

```bash
git clone <repo>
cd CourtReservationSystem
make                # builds src/*.cpp into ./bin/reservation
./bin/reservation   # run
```

### Clean

```bash
make clean
```

## Project layout

```
CourtReservationSystem/
├── include/        # Header files
│   ├── Coach.h
│   ├── Member.h
│   └── ...
├── src/            # Implementation
│   ├── main.cpp    # entry point
│   ├── ReservationSystem.cpp
│   └── ...
├── data/           # Sample CSVs (members.txt, courts.txt)
├── Makefile
└── tests/          # (optional) Catch2 unit tests
```

## Customisation

* Adjust `MAX_COURTS` or operating hours in `include/Config.h`.
* To switch to SQLite, stub out `FileStorage` in `src/Storage.cpp`.

## License

MIT – see `LICENSE`.
