declare name "ADAW_Saturation";
drive = hslider("drive", 1, 0.1, 12, 0.01);
trim = hslider("trim", 0.5, 0, 1, 0.001);
sat(x) = ma.tanh(x * drive) * trim;
process = sat, sat;

