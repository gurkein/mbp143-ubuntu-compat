#include <efi.h>

#ifndef GPU_INTEGRATED
#define GPU_INTEGRATED 0
#endif

#ifndef BOOT_WINDOWS
#define BOOT_WINDOWS 0
#endif

static EFI_GUID apple_gpu_guid = {
    0xfa4ce28d, 0xb62f, 0x4c99,
    {0x9c, 0xc3, 0x68, 0x15, 0x68, 0x6e, 0x30, 0xf9}
};
static EFI_GUID *apple_gpu_guid_ptr = &apple_gpu_guid;

#if BOOT_WINDOWS
static EFI_GUID global_variable_guid = {
    0x8be4df61, 0x93ca, 0x11d2,
    {0xaa, 0x0d, 0x00, 0xe0, 0x98, 0x03, 0x2b, 0x8c}
};

static BOOLEAN
contains_windows_loader(const UINT8 *data, UINTN size)
{
    static const CHAR16 path[] = L"\\EFI\\Microsoft\\Boot\\bootmgfw.efi";
    const UINTN path_size = sizeof(path) - sizeof(path[0]);
    UINTN offset;
    UINTN index;

    if (size < path_size)
        return FALSE;

    for (offset = 0; offset + path_size <= size; offset += sizeof(CHAR16)) {
        for (index = 0; index < path_size; index++) {
            UINT8 expected = ((const UINT8 *)path)[index];
            UINT8 actual = data[offset + index];

            if (actual >= 'A' && actual <= 'Z')
                actual = (UINT8)(actual + ('a' - 'A'));
            if (expected >= 'A' && expected <= 'Z')
                expected = (UINT8)(expected + ('a' - 'A'));
            if (actual != expected)
                break;
        }
        if (index == path_size)
            return TRUE;
    }
    return FALSE;
}

static BOOLEAN
boot_option_is_windows(EFI_SYSTEM_TABLE *system_table, UINT16 number)
{
    static const CHAR16 hex[] = L"0123456789ABCDEF";
    EFI_RUNTIME_SERVICES *runtime = system_table->RuntimeServices;
    EFI_BOOT_SERVICES *boot = system_table->BootServices;
    CHAR16 variable_name[] = L"Boot0000";
    UINT8 *load_option = NULL;
    UINTN load_option_size = 0;
    EFI_STATUS status;
    BOOLEAN found = FALSE;

    variable_name[4] = hex[(number >> 12) & 0xf];
    variable_name[5] = hex[(number >> 8) & 0xf];
    variable_name[6] = hex[(number >> 4) & 0xf];
    variable_name[7] = hex[number & 0xf];

    status = runtime->GetVariable(variable_name, &global_variable_guid,
                                  NULL, &load_option_size, NULL);
    if (status != EFI_BUFFER_TOO_SMALL)
        return FALSE;
    status = boot->AllocatePool(EfiLoaderData, load_option_size,
                                (VOID **)&load_option);
    if (EFI_ERROR(status))
        return FALSE;
    status = runtime->GetVariable(variable_name, &global_variable_guid,
                                  NULL, &load_option_size, load_option);
    if (!EFI_ERROR(status))
        found = contains_windows_loader(load_option, load_option_size);
    boot->FreePool(load_option);
    return found;
}

static EFI_STATUS
find_windows_boot(EFI_SYSTEM_TABLE *system_table, UINT16 *windows_boot)
{
    EFI_RUNTIME_SERVICES *runtime = system_table->RuntimeServices;
    EFI_BOOT_SERVICES *boot = system_table->BootServices;
    UINT16 *boot_order = NULL;
    UINTN boot_order_size = 0;
    EFI_STATUS status;
    UINTN entry;

    status = runtime->GetVariable(L"BootOrder", &global_variable_guid,
                                  NULL, &boot_order_size, NULL);
    if (status != EFI_BUFFER_TOO_SMALL)
        return status;

    status = boot->AllocatePool(EfiLoaderData, boot_order_size,
                                (VOID **)&boot_order);
    if (EFI_ERROR(status))
        return status;

    status = runtime->GetVariable(L"BootOrder", &global_variable_guid,
                                  NULL, &boot_order_size, boot_order);
    if (EFI_ERROR(status)) {
        boot->FreePool(boot_order);
        return status;
    }

    for (entry = 0; entry < boot_order_size / sizeof(UINT16); entry++) {
        UINT16 number = boot_order[entry];

        if (boot_option_is_windows(system_table, number)) {
            *windows_boot = number;
            boot->FreePool(boot_order);
            return EFI_SUCCESS;
        }
    }

    boot->FreePool(boot_order);

    /* Apple firmware can retain Windows outside BootOrder; scan normal IDs. */
    for (entry = 0; entry <= 0xff; entry++) {
        if (boot_option_is_windows(system_table, (UINT16)entry)) {
            *windows_boot = (UINT16)entry;
            return EFI_SUCCESS;
        }
    }
    return EFI_NOT_FOUND;
}
#endif

EFI_STATUS EFIAPI
efi_main(EFI_HANDLE image_handle, EFI_SYSTEM_TABLE *system_table)
{
    EFI_STATUS status;
    UINT8 preference[4] = {GPU_INTEGRATED ? 1 : 0, 0, 0, 0};
    UINT32 attributes = EFI_VARIABLE_NON_VOLATILE |
                        EFI_VARIABLE_BOOTSERVICE_ACCESS |
                        EFI_VARIABLE_RUNTIME_ACCESS;

    (void)image_handle;
#if BOOT_WINDOWS
    {
        UINT16 windows_boot;

        status = find_windows_boot(system_table, &windows_boot);
        if (EFI_ERROR(status))
            return status;
        status = system_table->RuntimeServices->SetVariable(
            L"BootNext", &global_variable_guid, attributes,
            sizeof(windows_boot), &windows_boot);
        if (EFI_ERROR(status))
            return status;
    }
#endif
    status = system_table->RuntimeServices->SetVariable(
        L"gpu-power-prefs", apple_gpu_guid_ptr, attributes,
        sizeof(preference), preference);
    if (EFI_ERROR(status)) {
#if BOOT_WINDOWS
        system_table->RuntimeServices->SetVariable(
            L"BootNext", &global_variable_guid, 0, 0, NULL);
#endif
        return status;
    }

    system_table->RuntimeServices->ResetSystem(
        EfiResetCold, EFI_SUCCESS, 0, NULL);
    return EFI_SUCCESS;
}
