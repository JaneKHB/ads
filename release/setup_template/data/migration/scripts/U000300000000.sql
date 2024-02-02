------------------------------------------------------------
------------------------------------------------------------
-- cnvset schema
------------------------------------------------------------
------------------------------------------------------------
create schema if not exists cnvset;
alter schema cnvset owner to rssadmin;

create table if not exists cnvset.server_config
(
    key   varchar(50)                                not null
        constraint server_config_pk
            primary key,
    value varchar(255) default ''::character varying not null
);

alter table cnvset.server_config
    owner to rssadmin;

create table if not exists cnvset.step_process
(
    id      varchar(50)                                      not null
        constraint step_process_pk
            primary key,
    created timestamp   default now()                        not null,
    step    varchar(20)                                      not null,
    client  varchar(50)                                      not null,
    status  varchar(20) default 'unknown'::character varying not null
);

alter table cnvset.step_process
    owner to rssadmin;

create unique index step_process_id_uindex
    on cnvset.step_process (id);

create table if not exists cnvset.system_log
(
    id     bigserial                                     not null
        constraint system_log_pk
            primary key,
    ts     timestamp   default now()                     not null,
    sys    varchar(30)                                   not null,
    key    varchar(100),
    lv     varchar(10) default 'info'::character varying not null,
    msg    varchar(512)                                  not null,
    module varchar(30)                                   not null
);

alter table cnvset.system_log
    owner to rssadmin;

------------------------------------------------------------
------------------------------------------------------------
-- cras_db schema
------------------------------------------------------------
------------------------------------------------------------
create schema if not exists cras_db;
alter schema cras_db owner to rssadmin;

create table if not exists cras_db.equipments
(
    machinename    text,
    fab_name       text,
    tool_serial    text,
    tooltype       text,
    tool_id        text,
    inner_tool_id  text,
    user_name      text,
    equipment_name text,
    equipment_id   text not null
        constraint equipments_pkey
            primary key
);

alter table cras_db.equipments
    owner to rssadmin;

create table if not exists cras_db.error_summary
(
    equipment_id   text not null
        constraint error_summary_equipment_id_fkey
            references cras_db.equipments(equipment_id)
            on update cascade on delete cascade,
    log_date       date not null,
    error_no       text not null,
    error_name     text,
    elapsed        time default '00:00:00'::time without time zone,
    error_rank     text,
    error_count    integer,
    error_category text,
    constraint error_summary_pkey
        primary key (equipment_id, log_date, error_no)
);

alter table cras_db.error_summary
    owner to rssadmin;

create table if not exists cras_db.mahalanobis_distance
(
    log_time     timestamptz        not null,
    equipment_id text             not null
        constraint mahalanobis_distance_equipment_id_fkey
            references cras_db.equipments(equipment_id)
            on update cascade on delete cascade,
    table_name   text             not null,
    colname1     text             not null,
    coldata1     double precision not null,
    colname2     text             not null,
    coldata2     double precision not null,
    item         text             not null,
    distance     real,
    quadrant     integer,
    constraint mahalanobis_distance_pkey
        primary key (log_time, equipment_id, item)
);

alter table cras_db.mahalanobis_distance
    owner to rssadmin;

create index mahalanobis_distance_log_time_equipment_id_item_quadrant_idx
    on cras_db.mahalanobis_distance (log_time, equipment_id, item, quadrant);

-- arcnetlog_analysis_async
create table cras_db.arcnetlog_analysis_async
(
    equipment_id    text         not null
        constraint arcnetlog_analysis_async_equipment_name_fkey
            references cras_db.equipments(equipment_id)
            on update cascade on delete cascade,
    equipment_name    text         not null,
    time            timestamptz(6) not null,
    counter         varchar(16)  not null,
    unit_id         varchar(16)  not null,
    axis_id         varchar(16)  not null,
    axis_name       varchar(16),
    run_count       integer,
    run_direction_1 varchar(16),
    stop_posi_1     varchar(16),
    run_range_1     varchar(16),
    run_direction_2 varchar(16),
    stop_posi_2     varchar(16),
    run_range_2     varchar(16),
    run_direction_3 varchar(16),
    stop_posi_3     varchar(16),
    run_range_3     varchar(16),
    run_direction_4 varchar(16),
    stop_posi_4     varchar(16),
    run_range_4     varchar(16),
    run_direction_5 varchar(16),
    stop_posi_5     varchar(16),
    run_range_5     varchar(16),
    run_direction_6 varchar(16),
    stop_posi_6     varchar(16),
    run_range_6     varchar(16),
    constraint arcnetlog_analysis_async_pkey
        primary key (equipment_id, time, counter, unit_id, axis_id)
);

alter table cras_db.arcnetlog_analysis_async
    owner to rssadmin;

create index arcnetlog_analysis_async_time_equipment_name_axis_name_run__idx
    on cras_db.arcnetlog_analysis_async (time, equipment_id, axis_name, run_count);

-- arcnetlog_analysis_data
create table cras_db.arcnetlog_analysis_data
(
    equipment_id text         not null
        constraint arcnetlog_analysis_data_equipment_name_fkey
            references cras_db.equipments(equipment_id)
            on update cascade on delete cascade,
    equipment_name    text         not null,
    item         integer      not null,
    name         varchar(128),
    time_start   timestamptz(6) not null,
    time_end     timestamptz(6) not null,
    timer_ms     integer      not null,
    posi_start   integer,
    posi_end     integer,
    range        integer,
    misalignment integer,
    constraint arcnetlog_analysis_data_pkey
        primary key (equipment_id, item, time_start, time_end, timer_ms)
);

alter table cras_db.arcnetlog_analysis_data
    owner to rssadmin;

create index arcnetlog_analysis_data_time_start_equipment_name_name_idx
    on cras_db.arcnetlog_analysis_data (time_start, equipment_id, name);

-- arcnetlog_analysis_timediff
create table cras_db.arcnetlog_analysis_timediff
(
    equipment_id text         not null
        constraint arcnetlog_analysis_data_equipment_name_fkey
            references cras_db.equipments(equipment_id)
            on update cascade on delete cascade,
    equipment_name    text         not null,
    calculate_name varchar(128),
    time_start     timestamptz(6),
    max_item       varchar(128),
    max_timer_ms   integer,
    min_item       varchar(128),
    min_timer_ms   integer,
    time_diff      integer,
    time_ave       integer,
    constraint arcnetlog_analysis_timediff_pkey
        primary key (equipment_id, calculate_name, time_start)
);

alter table cras_db.arcnetlog_analysis_timediff
    owner to rssadmin;

create index arcnetlog_analysis_timediff_time_start_equipment_name_calculate_name_idx
    on cras_db.arcnetlog_analysis_timediff (time_start, equipment_id, calculate_name);

-- liftbarvac_analysis
create table cras_db.liftbarvac_analysis
(
    equipment_id  text         not null
        constraint liftbarvac_analysis_equipment_name_fkey
            references cras_db.equipments(equipment_id)
            on update cascade on delete cascade,
    equipment_name    text         not null,
    log_time      timestamptz(6) not null,
    vac_time_mean numeric(15, 3),
    vac_time_reg  numeric(15, 5),
    constraint liftbarvac_analysis_pkey
        primary key (equipment_id, log_time)
);

alter table cras_db.liftbarvac_analysis
    owner to rssadmin;

create table cras_db.liftbarvac_merged
(
    equipment_id text         not null
        constraint liftbarvac_merged_equipment_name_fkey
            references cras_db.equipments(equipment_id)
            on update cascade on delete cascade,
    equipment_name    text         not null,
    log_time     timestamptz(6) not null,
    device       varchar(64),
    process      varchar(64),
    glass_id     varchar(64),
    vac_time     integer,
    constraint liftbarvac_merged_pkey
        primary key (equipment_id, log_time)
);

alter table cras_db.liftbarvac_merged
    owner to rssadmin;

------------------------------------------------------------
------------------------------------------------------------
-- userdata schema
------------------------------------------------------------
------------------------------------------------------------
create schema if not exists userdata;
alter schema userdata owner to rssadmin;

create table if not exists userdata.collect_separately_info
(
    equipment_id                        varchar(64) not null
        constraint collect_separately_info_pkey
            primary key
        constraint collect_separately_info_equipment_id_fkey
            references cras_db.equipments
            on delete cascade,
    iscollect_ai                        boolean,
    iscollect_liplus                    boolean,
    iscollect_scan                      boolean,
    ai_collected_time                   varchar(64),
    liplus_normallog_collected_time     varchar(64),
    liplus_process_collected_time       varchar(64),
    liplus_focuslog_collected_time      varchar(64),
    liplus_statusmonitor_collected_time varchar(64),
    liplus_cras_collected_time          varchar(64),
    liplus_error_summary_collected_time varchar(64),
    liplus_running_rate_collected_time  varchar(64),
    scan_collected_time                 varchar(64),
    scan_cog_collected_time             varchar(64),
    scan_mpsync_collected_time          varchar(64),
    iscollect_arcnetlog                 boolean,
    arcnetlog_collected_time            varchar(64),
    arcnetlog_analysis_time             varchar(64),
    liplus_vftp_collected_time          varchar(64),
    iscollect_liftbarvac                boolean     default false,
    liftbarvac_collected_time           varchar(64) default '2021-12-01 00:00:00'::character varying,
    liftbarvac_last_analysis_logtime    varchar(64) default '2021-12-01 00:00:00.0000'::character varying
);

alter table userdata.collect_separately_info
    owner to rssadmin;

------------------------------------------------------------
------------------------------------------------------------
-- fragments schema
------------------------------------------------------------
------------------------------------------------------------
create schema if not exists fragments;
alter schema fragments owner to rssadmin;

create table if not exists fragments.adccomp
(
    id                                   serial                   not null
        constraint adccomp_pkey
            primary key,
    equipment_name                       varchar(128)             not null,
    device                               varchar(128),
    process                              varchar(128),
    plate                                integer,
    step                                 integer,
    base_layer_machine_no                integer,
    glass_id                             varchar(128),
    lot_id                               varchar(128),
    log_time                             timestamp with time zone not null,
    chuck                                varchar(128),
    data_condition                       varchar(128),
    measured_mx_sub_adcoffset_p2p3       integer,
    measured_mx_p1                       integer,
    measured_mx_sub_adcoffset_p2p1       integer,
    measuredoffset_arc_u_drive           integer,
    measuredoffset_arc_l_drive           integer,
    measuredoffset_arc_ave               integer,
    measuredoffset_arc_drive             integer,
    masktemp_my                          integer,
    measured_arc                         integer,
    masktemp_mx                          integer,
    measuredoffset_mx_ave                integer,
    measuredoffset_mx_drive              integer,
    measuredoffset_yaw_up                integer,
    measuredoffset_yaw_low               integer,
    measuredoffset_my_up                 integer,
    measuredoffset_my_low                integer,
    measuredoffset_dr_up                 integer,
    measuredoffset_dr_low                integer,
    measuredoffset_mx_sub_adcoffset_p2p3 integer,
    measuredoffset_mx_p3                 integer,
    measuredoffset_mx_sub_adcoffset_p2p1 integer,
    measuredoffset_mx_p2                 integer,
    measuredoffset_mx_p1                 integer,
    measured_yaw_low                     integer,
    measured_mx                          integer,
    measured_my_low                      integer,
    measured_yaw_up                      integer,
    measured_dr_low                      integer,
    measured_my_up                       integer,
    measured_mx_p3                       integer,
    measured_dr_up                       integer,
    measured_mx_p2                       integer,
    log_idx                              integer                  not null,
    shot_key                             varchar(128)             not null
);

alter table fragments.adccomp
    owner to rssadmin;

create table if not exists fragments.adcmeasure
(
    id                     serial                   not null
        constraint adcmeasure_pkey
            primary key,
    equipment_name         varchar(128)             not null,
    device                 varchar(128),
    process                varchar(128),
    plate                  integer,
    step                   integer,
    p1_measnum             integer,
    p2_measnum             integer,
    p3_measnum             integer,
    baselayermachine_no    integer,
    glass_id               varchar(128),
    lot_id                 varchar(128),
    log_time               timestamp with time zone not null,
    chuck                  varchar(128),
    logicalposition_x      integer,
    logicalposition_y      integer,
    physicalposition_y     integer,
    physicalposition_theta integer,
    p3_yr                  integer,
    physicalposition_x     integer,
    p3_yl                  integer,
    p3_xr                  integer,
    p2_yr                  integer,
    p3_xl                  integer,
    p2_yl                  integer,
    p2_xr                  integer,
    p1_yr                  integer,
    p2_xl                  integer,
    p1_yl                  integer,
    p1_xr                  integer,
    p1_xl                  integer,
    logicalposition_theta  varchar(128),
    log_idx                integer                  not null,
    step_num               integer,
    shot_key               varchar(128)             not null
);

alter table fragments.adcmeasure
    owner to rssadmin;

create table if not exists fragments.django_migrations
(
    id      serial                   not null
        constraint django_migrations_pkey
            primary key,
    app     varchar(255)             not null,
    name    varchar(255)             not null,
    applied timestamp with time zone not null
);

alter table fragments.django_migrations
    owner to rssadmin;

create table if not exists fragments.evaluationmonitor
(
    id                    serial                   not null
        constraint evaluationmonitor_pkey
            primary key,
    equipment_name        varchar(128)             not null,
    device                varchar(128),
    process               varchar(128),
    plate                 integer,
    step                  integer,
    pos                   varchar(128),
    result                varchar(128),
    evaluation_left       integer,
    evaluation_right      integer,
    hg_left               double precision,
    hg_right              double precision,
    led1_left             integer,
    led1_right            integer,
    led2_left             integer,
    led2_right            integer,
    white_led_left_value  integer,
    white_led_left_bpf    varchar(128),
    white_led_right_value integer,
    white_led_right_bpf   varchar(128),
    half_wave_plate_left  integer,
    half_wave_plate_right integer,
    glass_id              varchar(128),
    lot_id                varchar(128),
    log_time              timestamp with time zone not null,
    chuck                 varchar(128),
    ps_z                  integer,
    relay_lens_left       integer,
    relay_lens_right      integer,
    log_idx               integer                  not null,
    shot_key              varchar(128)             not null
);

alter table fragments.evaluationmonitor
    owner to rssadmin;

create table if not exists fragments.image
(
    bmp_path          varchar(256)             not null
        constraint image_pkey
            primary key,
    raw_path          varchar(256),
    jpeg_path         varchar(256)             not null,
    datetime_image    timestamp with time zone not null,
    scope             varchar(16)              not null,
    position          varchar(16)              not null,
    l_or_r            varchar(16)              not null,
    average_num       integer                  not null,
    errorjudgement    boolean                  not null,
    errorfactor_names varchar(128),
    errorbefore_num   integer,
    parameter_path    varchar(256),
    shot_key          varchar(128)             not null
);

alter table fragments.image
    owner to rssadmin;

create index image_bmp_path_297c3dc9_like
    on fragments.image (bmp_path varchar_pattern_ops);

create table if not exists fragments.mpsync_error_collected
(
    unique_key     varchar(256)             not null
        constraint mpsync_error_collected_pkey
            primary key,
    equipment_name varchar(128)             not null,
    step           integer,
    glass_id       varchar(128)             not null,
    log_time       timestamp with time zone not null,
    parameter_name varchar(128)             not null,
    tolerance      integer,
    parameter_num  integer,
    is_collected   boolean
);

alter table fragments.mpsync_error_collected
    owner to rssadmin;

create index mpsync_error_collected_unique_key_a6730247_like
    on fragments.mpsync_error_collected (unique_key varchar_pattern_ops);

create table if not exists fragments.plate
(
    plate_key            varchar(128)             not null
        constraint plate_pkey
            primary key,
    user_fab             varchar(32)              not null,
    equipment_name       varchar(128)             not null,
    mark_type            varchar(32)              not null,
    datetime_plate       timestamp with time zone not null,
    glass_id             varchar(32)              not null,
    plate_no             integer                  not null,
    job_name             varchar(128),
    errorjudgement_plate boolean                  not null,
    equipment_key        varchar(128)             not null
);

alter table fragments.plate
    owner to rssadmin;

create table if not exists fragments.scan_plate
(
    plate_key            varchar(128)             not null
        constraint scan_plate_pkey
            primary key,
    user_fab             varchar(32)              not null,
    equipment_name       varchar(128)             not null,
    datetime_plate       timestamp with time zone not null,
    glass_id             varchar(32)              not null,
    plate_no             integer                  not null,
    job_name             varchar(128),
    errorjudgement_plate boolean                  not null,
    fdacq_flag_plate     boolean                  not null,
    equipment_key        varchar(128)             not null,
    normal_flag_plate    boolean                  not null
);

alter table fragments.scan_plate
    owner to rssadmin;

create index scan_plate_plate_key_5e2984fd_like
    on fragments.scan_plate (plate_key varchar_pattern_ops);

create table if not exists fragments.scan_shot
(
    shot_key            varchar(128)             not null
        constraint scan_shot_pkey
            primary key,
    glass_id            varchar(32)              not null,
    datetime_shot       timestamp with time zone not null,
    shot_no             integer                  not null,
    errorjudgement_shot boolean                  not null,
    fdacq_flag_shot     boolean                  not null,
    plate_key           varchar(128)             not null
);

alter table fragments.scan_shot
    owner to rssadmin;

create index scan_shot_shot_key_de09ba5d_like
    on fragments.scan_shot (shot_key varchar_pattern_ops);

create table if not exists fragments.scan_spectrogram
(
    spectrogram_path varchar(256)             not null
        constraint scan_spectrogram_pkey
            primary key,
    datetime_scan    timestamp with time zone not null,
    index_num        integer                  not null,
    errorjudgement   boolean                  not null,
    shot_key         varchar(128)             not null
);

alter table fragments.scan_spectrogram
    owner to rssadmin;

create index scan_spectrogram_spectrogram_path_2f39b651_like
    on fragments.scan_spectrogram (spectrogram_path varchar_pattern_ops);

create table if not exists fragments.scan_spectrogram_detail
(
    id                            serial           not null
        constraint scan_spectrogram_detail_pkey
            primary key,
    filepath                      varchar(256)     not null,
    time                          double precision not null,
    errp_psx_frequency            integer,
    errp_psx_powerspectrum        integer,
    errp_psy_frequency            integer,
    errp_psy_powerspectrum        integer,
    errp_pst_frequency            integer,
    errp_pst_powerspectrum        integer,
    errp_psz_frequency            integer,
    errp_psz_powerspectrum        integer,
    errp_pit_frequency            integer,
    errp_pit_powerspectrum        integer,
    errp_roll_frequency           integer,
    errp_roll_powerspectrum       integer,
    errv_psy_frequency            integer,
    errv_psy_powerspectrum        integer,
    errp_msx_frequency            integer,
    errp_msx_powerspectrum        integer,
    errp_msy_frequency            integer,
    errp_msy_powerspectrum        integer,
    errp_mst_frequency            integer,
    errp_mst_powerspectrum        integer,
    syncerr_x_frequency           integer,
    syncerr_x_powerspectrum       integer,
    syncerr_y_frequency           integer,
    syncerr_y_powerspectrum       integer,
    syncerr_z_frequency           integer,
    syncerr_z_powerspectrum       integer,
    err_mnt_x_frequency           integer,
    err_mnt_x_powerspectrum       integer,
    err_mnt_y_frequency           integer,
    err_mnt_y_powerspectrum       integer,
    err_mnt_t_frequency           integer,
    err_mnt_t_powerspectrum       integer,
    err_mnt_z_frequency           integer,
    err_mnt_z_powerspectrum       integer,
    err_mnt_pit_frequency         integer,
    err_mnt_pit_powerspectrum     integer,
    err_mnt_rol_frequency         integer,
    err_mnt_rol_powerspectrum     integer,
    err_mnt_phi_frequency         integer,
    err_mnt_phi_powerspectrum     integer,
    acc_mnt_x_frequency           integer,
    acc_mnt_x_powerspectrum       integer,
    acc_mnt_y_frequency           integer,
    acc_mnt_y_powerspectrum       integer,
    acc_mnt_t_frequency           integer,
    acc_mnt_t_powerspectrum       integer,
    acc_mnt_z_frequency           integer,
    acc_mnt_z_powerspectrum       integer,
    acc_mnt_pit_frequency         integer,
    acc_mnt_pit_powerspectrum     integer,
    acc_mnt_rol_frequency         integer,
    acc_mnt_rol_powerspectrum     integer,
    acc_mnt_phi_frequency         integer,
    acc_mnt_phi_powerspectrum     integer,
    acc_lsr_psx_frequency         integer,
    acc_lsr_psx_powerspectrum     integer,
    acc_lsr_psy_frequency         integer,
    acc_lsr_psy_powerspectrum     integer,
    acc_lsr_msx_frequency         integer,
    acc_lsr_msx_powerspectrum     integer,
    acc_lsr_msyr_frequency        integer,
    acc_lsr_msyr_powerspectrum    integer,
    acc_lsr_msyl_frequency        integer,
    acc_lsr_msyl_powerspectrum    integer,
    acc_opt_x_frequency           integer,
    acc_opt_x_powerspectrum       integer,
    acc_opt_y_frequency           integer,
    acc_opt_y_powerspectrum       integer,
    acc_opt_yaw_frequency         integer,
    acc_opt_yaw_powerspectrum     integer,
    acc_opt_z_frequency           integer,
    acc_opt_z_powerspectrum       integer,
    acc_opt_pit_frequency         integer,
    acc_opt_pit_powerspectrum     integer,
    acc_opt_rol_frequency         integer,
    acc_opt_rol_powerspectrum     integer,
    acc_convex_x_frequency        integer,
    acc_convex_x_powerspectrum    integer,
    acc_convex_y_frequency        integer,
    acc_convex_y_powerspectrum    integer,
    acc_convex_yaw_frequency      integer,
    acc_convex_yaw_powerspectrum  integer,
    acc_convex_z_frequency        integer,
    acc_convex_z_powerspectrum    integer,
    acc_convex_pit_frequency      integer,
    acc_convex_pit_powerspectrum  integer,
    acc_convex_rol_frequency      integer,
    acc_convex_rol_powerspectrum  integer,
    acc_concave_x_frequency       integer,
    acc_concave_x_powerspectrum   integer,
    acc_concave_y_frequency       integer,
    acc_concave_y_powerspectrum   integer,
    acc_concave_yaw_frequency     integer,
    acc_concave_yaw_powerspectrum integer,
    acc_concave_z_frequency       integer,
    acc_concave_z_powerspectrum   integer,
    acc_concave_pit_frequency     integer,
    acc_concave_pit_powerspectrum integer,
    acc_concave_rol_frequency     integer,
    acc_concave_rol_powerspectrum integer
);

alter table fragments.scan_spectrogram_detail
    owner to rssadmin;

create table if not exists fragments.scan_spectrum
(
    spectrum_path  varchar(256)             not null
        constraint scan_spectrum_pkey
            primary key,
    datetime_scan  timestamp with time zone not null,
    errorjudgement boolean                  not null,
    shot_key       varchar(128)             not null
);

alter table fragments.scan_spectrum
    owner to rssadmin;

create index scan_spectrum_spectrum_path_77b29fa6_like
    on fragments.scan_spectrum (spectrum_path varchar_pattern_ops);

create table if not exists fragments.scan_spectrum_detail
(
    id              serial       not null
        constraint scan_spectrum_detail_pkey
            primary key,
    filepath        varchar(256) not null,
    frequency       integer,
    errp_psx        integer,
    errp_psy        integer,
    errp_pst        integer,
    errp_psz        integer,
    errp_pit        integer,
    errp_roll       integer,
    errv_psy        integer,
    errp_msx        integer,
    errp_msy        integer,
    errp_mst        integer,
    syncerr_x       integer,
    syncerr_y       integer,
    syncerr_z       integer,
    err_mnt_x       integer,
    err_mnt_y       integer,
    err_mnt_t       integer,
    err_mnt_z       integer,
    err_mnt_pit     integer,
    err_mnt_rol     integer,
    err_mnt_phi     integer,
    acc_mnt_x       integer,
    acc_mnt_y       integer,
    acc_mnt_t       integer,
    acc_mnt_z       integer,
    acc_mnt_pit     integer,
    acc_mnt_rol     integer,
    acc_mnt_phi     integer,
    acc_lsr_psx     integer,
    acc_lsr_psy     integer,
    acc_lsr_msx     integer,
    acc_lsr_msyr    integer,
    acc_lsr_msyl    integer,
    acc_opt_x       integer,
    acc_opt_y       integer,
    acc_opt_yaw     integer,
    acc_opt_z       integer,
    acc_opt_pit     integer,
    acc_opt_rol     integer,
    acc_convex_x    integer,
    acc_convex_y    integer,
    acc_convex_yaw  integer,
    acc_convex_z    integer,
    acc_convex_pit  integer,
    acc_convex_rol  integer,
    acc_concave_x   integer,
    acc_concave_y   integer,
    acc_concave_yaw integer,
    acc_concave_z   integer,
    acc_concave_pit integer,
    acc_concave_rol integer
);

alter table fragments.scan_spectrum_detail
    owner to rssadmin;

create table if not exists fragments.shot
(
    shot_key            varchar(128)             not null
        constraint shot_pkey
            primary key,
    glass_id            varchar(32)              not null,
    datetime_shot       timestamp with time zone not null,
    shot_no             integer                  not null,
    errorjudgement_shot boolean                  not null,
    errorfactor_id      integer,
    errorfactor_names   varchar(128),
    imagefilter_id      integer,
    imagefilter_name    varchar(128),
    plate_key           varchar(128)             not null,
    datetime_shot_error timestamp with time zone
);

alter table fragments.shot
    owner to rssadmin;

create index shot_shot_key_219c79d6_like
    on fragments.shot (shot_key varchar_pattern_ops);

------------------------------------------------------------
------------------------------------------------------------
-- public schema
------------------------------------------------------------
------------------------------------------------------------
create type header_type as enum ('with_header', 'without_header');

alter type header_type owner to rssadmin;

create type job_category as enum ('convert', 'summary', 'cras', 'version');

alter type job_category owner to rssadmin;

create type request_status as enum ('idle', 'running', 'error', 'success', 'cancel');

alter type request_status owner to rssadmin;

create type request_type as enum ('local', 'rapid');

alter type request_type owner to rssadmin;
