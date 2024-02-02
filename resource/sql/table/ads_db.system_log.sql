create table ads_db.system_log
(
    id     bigserial
        constraint system_log_pk
            primary key,
    ts     timestamp   default now()                     not null,
    sys    varchar(30)                                   not null,
    key    varchar(100),
    lv     varchar(10) default 'info'::character varying not null,
    msg    text                                  not null,
    module varchar(30)                                   not null
);