-- Some testing data to fill up the pyoseo database while testing

INSERT INTO 'user' ('admin', name, e_mail, full_name, password)
VALUES 
(1, 'ricardogsilva', 'ricardo.silva@ipma.pt', 'Ricardo Garcia Silva', 'pyoseo'),
(0, 'jmacedo', 'joao.macedo@ipma.pt', 'Joao Macedo', 'pyoseo'),
(0, 'scoelho', 'sandra.coelho@ipma.pt', 'Sandra Coelho', 'pyoseo');

INSERT INTO 'order' (status, created_on, status_changed_on, reference, remark,
                     packaging, priority, order_type, additional_status_info,
                     mission_specific_status_info)
VALUES 
('Submitted', datetime(), datetime(), NULL, NULL, 'bzip2', 'STANDARD',
'normal_order', NULL, NULL),
('Submitted', datetime(), datetime(), 'a sample reference', 'a sample remark',
'bzip2', 'STANDARD', 'normal_order', NULL, NULL),
('Submitted', datetime(), datetime(), 'a sample reference', 'a sample remark',
'bzip2', 'STANDARD', 'normal_order', NULL, NULL),
('Submitted', datetime(), datetime(), 'a sample reference', 'a sample remark',
'bzip2', 'STANDARD', 'normal_order', NULL, NULL),
('Submitted', datetime(), datetime(), 'a sample reference', 'a sample remark',
'bzip2', 'STANDARD', 'normal_order', 'some additional status information',
'some mission specific status information');

INSERT INTO 'normal_order' (id, user_id)
VALUES
(1, 1),
(2, 1),
(3, 1),
(4, 2),
(5, 2);

INSERT INTO 'order_item' (order_id, catalog_id)
VALUES 
(1, '12345'),
(1, '12346'),
(1, '12347'),
(1, '12348'),
(1, '12349'),
(1, '12350'),
(2, '12345'),
(2, '12346'),
(2, '12352'),
(2, '12353'),
(2, '12354');
