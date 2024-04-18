
; r0 = address of BattleParams struct
; r1 = battler ID of party to be built
; r2 = heap ID for any allocations
TrainerData_BuildParty:
    push    {r3-r7, lr}
    ; TODO: Stack allocation
    mov     r4, r0          ; r4 = address of BattleParams struct
    mov     r5, r1          ; r5 = battler ID
    mov     r6, r2          ; r6 = heap ID
    str     r5, [sp, #0x20] ; sp[0x20] = battler ID
    str     r6, [sp, #0x24] ; sp[0x24] = heap ID
    lsl     r7, r1, #2
    add     r7, r0, r7      ; r7 = relative memory offset of any of the battler's array-entries in the struct

    ; Cache the current RNG seed
    bl      LCRNG_GetSeed   ; r0 = current RNG seed
    str     r0, [sp, #0x10] ; sp[0x10] = current RNG seed

    ; Initialize the trainer's Party struct
    ldr     r0, [r7, #0x4]  ; r0 = memory offset of battler's Party struct in BattleParams struct
    mov     r1, #6          ; r1 = max party capacity
    bl      Party_InitWithCapacity

    ; Allocate memory for a new Pokemon struct
    mov     r0, r6          ; r0 = heap ID
    bl      Pokemon_New
    str     r0, [sp, #0x14] ; sp[0x14] = Pokemon struct address

    ; Allocate memory for the trainer party data buffer
    mov     r0, r6          ; r0 = heap ID
    mov     r1, #0x6C       ; r1 = max party capacity * max size of a trainer mon struct
    bl      Heap_AllocFromHeap
    str     r0, [sp, #0x18] ; sp[0x18] = read buffer address

    ; Load the party data from the trpoke.narc into the read buffer
    mov     r1, r0          ; r1 = read buffer address
    ldr     r0, [r7, #0x18] ; r0 = battler's trainer ID (from the BattleParams struct)
    bl      TrainerData_LoadParty

    ; Get the trainer's gender
    mov     r0, #0x34       ; r0 = size of TrainerData struct
    mov     r3, r7
    mul     r3, r0
    add     r0, r4, r3
    ldrb    r0, [r0, #0x29] ; r0 = battler's trainer class (e.g., "Youngster")
    strb    r0, [sp, #0x1C] ; sp[0x1C] = battler's trainer class
    bl      TrainerClass_Gender ; r0 = battler's trainer gender

    ; Determine the magic gender-specific modifier for the RNG seeding
    mov     r3, #0x78       ; r3 = default gender modifier
    lsl     r2, r0, #4      ; r2 = one of 0x00 (male), 0x10 (female), or 0x20 (genderless)
    mov     r0, #0x10
    and     r2, r0          ; r2 = one of 0x00 (male, genderless) or 0x10 (female)
    add     r3, r3, r2
    strb    r3, [sp, #0x1D] ; sp[0x1D] = magic gender-specific RNG seed modifier

    ; Read each of the trainer's Pokemon from the read buffer
    mov     r5, #0          ; r5 = loop counter
    mov     r0, #0x34       ; r0 = size of TrainerData struct
    mov     r3, r7
    mul     r3, r0
    add     r0, r4, r3
    ldrb    r6, [r0, #0x2B] ; r6 = number of party members to read

TrainerData_BuildParty_BuildMon:
    ; Common (base) fields:
    ;   - dv u8
    ;   - ability u8 (new to Platinum)
    ;   - level u16
    ;   - species+form u16
    ;   - ball seal u16 (always last)
    ;
    ; Optional fields (determined by the trainer type as a bitmask):
    ;   - item (u16)        -- bit 1 is ON
    ;   - moves (u16[4])    -- bit 0 is ON
