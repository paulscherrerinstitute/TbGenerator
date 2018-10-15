------------------------------------------------------------------------------
-- Copyright (c) 2018 by Paul Scherrer Institute, Switzerland
--  All rights reserved.
--  Authors: Oliver Bruendler
------------------------------------------------------------------------------

------------------------------------------------------------------------------
-- Description
------------------------------------------------------------------------------
-- This is a very basic asynchronous FIFO. The clocks can be fully asynchronous
-- (unrelated). It  has optional level- and almost-full/empty ports.
------------------------------------------------------------------------------
-- Libraries
------------------------------------------------------------------------------
library ieee;
	use ieee.std_logic_1164.all;
	use ieee.numeric_std.all;

library work;
	use work.psi_common_logic_pkg.all;
	use work.psi_common_math_pkg.all;
	
-- $$ PROCESSES=Input,Output $$

------------------------------------------------------------------------------
-- Entity Declaration
------------------------------------------------------------------------------
entity psi_common_async_fifo is
	generic (
		Width_g			: positive		:= 16;	-- $$ EXPORT=true $$
		Depth_g			: positive		:= 32;	-- $$ EXPORT=true; funky=bla $$
		AlmFullOn_g		: boolean		:= false;-- $$ EXPORT=false,funky=blubb $$
		AlmFullLevel_g	: natural		:= 28; --$$CONSTANT=12$$
		AlmEmptyOn_g	: boolean		:= false;
		AlmEmptyLevel_g	: natural		:= 4
	);
	port (
		-- Control Ports
		InClk		: in	std_logic;	-- $$ TYPE=CLK; FREQ=100e6; PROC=Input $$
		InRst		: in	std_logic;	-- $$ TYPE=RST; CLK=InClk $$
		OutClk		: in 	std_logic;	-- $$ TYPE=CLK; FREQ=125e6; Proc=Output $$
		OutRst		: in 	std_logic;	-- $$ TYPE=RST; CLK=OutClk $$

		-- Input Data
		InData		: in	std_logic_vector(Width_g-1 downto 0) := (others => '0');	-- $$ PROC=Input$$
		InVld		: in	std_logic;													-- $$ PROC=INPUT$$
		InRdy		: out	std_logic;	-- not full	$$PROC=input$$

		-- Output Data
		OutData		: out	std_logic_vector(Width_g-1 downto 0);	-- $$ PROC=Output$$
		OutVld		: out	std_logic;	-- not empty				-- $$ PROC=Output$$
		OutRdy		: in	std_logic := '1';						-- $$ PROC=Output,Input$$

		-- Input Status
		InFull		: out	std_logic;
		InEmpty		: out	std_logic;
		InAlmFull 	: out	std_logic;
		InAlmEmpty	: out	std_logic;
		InLevel		: out	std_logic_vector(log2ceil(Depth_g) downto 0);

		-- Output Status
		OutFull		: out	std_logic; -- $$ PROC=Input,Output $$
		OutEmpty	: out	std_logic;
		OutAlmFull	: out	std_logic;
		OutAlmEmpty : out 	std_logic;
		OutLevel	: out	std_logic_vector(log2ceil(Depth_g) downto 0)
	);
end entity;

------------------------------------------------------------------------------
-- Architecture Declaration
------------------------------------------------------------------------------
architecture rtl of psi_common_async_fifo is


	type two_process_in_r is record
		WrAddr			: unsigned(log2ceil(Depth_g) downto 0);				-- One additional bit for full/empty detection
		WrAddrGray		: std_logic_vector(log2ceil(Depth_g) downto 0);
		RdAddrGraySync	: std_logic_vector(log2ceil(Depth_g) downto 0);
		RdAddrGray		: std_logic_vector(log2ceil(Depth_g) downto 0);
		RdAddr			: unsigned(log2ceil(Depth_g) downto 0);
	end record;

	type two_process_out_r is record
		RdAddr			: unsigned(log2ceil(Depth_g) downto 0);				-- One additional bit for full/empty detection
		RdAddrGray		: std_logic_vector(log2ceil(Depth_g) downto 0);
		WrAddrGraySync	: std_logic_vector(log2ceil(Depth_g) downto 0);
		WrAddrGray		: std_logic_vector(log2ceil(Depth_g) downto 0);
		WrAddr			: unsigned(log2ceil(Depth_g) downto 0);
	end record;

	signal ri, ri_next	: two_process_in_r;
	signal ro, ro_next	: two_process_out_r;

	signal RstInInt				: std_logic;
	signal RstOutInt			: std_logic;
	signal RamWr				: std_logic;
	signal RamRdAddr			: std_logic_vector(log2ceil(Depth_g)-1 downto 0);

	attribute syn_srlstyle : string;
    attribute syn_srlstyle of ri : signal is "registers";
    attribute syn_srlstyle of ro : signal is "registers";

	attribute shreg_extract : string;
    attribute shreg_extract of ri : signal is "no";
    attribute shreg_extract of ro : signal is "no";

	attribute ASYNC_REG : string;
    attribute ASYNC_REG of ri : signal is "TRUE";
    attribute ASYNC_REG of ro : signal is "TRUE";


begin
	--------------------------------------------------------------------------
	-- Assertions
	--------------------------------------------------------------------------
	assert log2(Depth_g) = log2ceil(Depth_g) report "###ERROR###: psi_common_async_fifo: only power of two Depth_g is allowed" severity error;

	--------------------------------------------------------------------------
	-- Combinatorial Process
	--------------------------------------------------------------------------
	p_comb : process(InVld, OutRdy, ri, ro)
		variable vi				: two_process_in_r;
		variable vo				: two_process_out_r;
		variable InLevel_v		: unsigned(log2ceil(Depth_g) downto 0);
		variable OutLevel_v		: unsigned(log2ceil(Depth_g) downto 0);
	begin
		-- *** hold variables stable ***
		vi := ri;
		vo := ro;

		-- *** Write Side ***
		-- Defaults
		InRdy		<= '0';
		InFull		<= '0';
		InEmpty		<= '0';
		InAlmFull	<= '0';
		InAlmEmpty	<= '0';
		RamWr		<= '0';

		-- Level Detection
		InLevel_v	:= ri.WrAddr - ri.RdAddr;
		InLevel		<= std_logic_vector(InLevel_v);

		-- Full
		if InLevel_v = Depth_g then
			InFull	<= '1';
		else
			InRdy 	<= '1';
			-- Execute Write
			if InVld = '1' then
				vi.WrAddr	:= ri.WrAddr + 1;
				RamWr 		<= '1';
			end if;
		end if;

		-- Status Detection
		if InLevel_v = 0 then
			InEmpty <= '1';
		end if;
		if InLevel_v >= AlmFullLevel_g and AlmFullOn_g then
			InAlmFull <= '1';
		end if;
		if InLevel_v <= AlmEmptyLevel_g and AlmEmptyOn_g then
			InAlmEmpty <= '1';
		end if;

		-- *** Read Side ***
		-- Defaults
		OutVld		<= '0';
		OutFull		<= '0';
		OutEmpty	<= '0';
		OutAlmFull	<= '0';
		OutAlmEmpty	<= '0';

		-- Level Detection
		OutLevel_v	:= ro.WrAddr - ro.RdAddr;
		OutLevel	<= std_logic_vector(OutLevel_v);

		-- Empty
		if OutLevel_v = 0 then
			OutEmpty	<= '1';
		else
			OutVld 		<= '1';
			-- Execute read
			if OutRdy = '1' then
				vo.RdAddr	:= ro.RdAddr + 1;
			end if;
		end if;
		RamRdAddr <= std_logic_vector(vo.RdAddr(log2ceil(Depth_g)-1 downto 0));

		-- Status Detection
		if OutLevel_v = Depth_g then
			OutFull	<= '1';
		end if;
		if OutLevel_v >= AlmFullLevel_g and AlmFullOn_g then
			OutAlmFull <= '1';
		end if;
		if OutLevel_v <= AlmEmptyLevel_g and AlmEmptyOn_g then
			OutAlmEmpty <= '1';
		end if;

		-- *** Address Clock domain crossings ***
		-- Bin->Gray is simple, can be done without additional FF
		vi.WrAddrGray	:= BinaryToGray(std_logic_vector(vi.WrAddr));
		vo.RdAddrGray	:= BinaryToGray(std_logic_vector(vo.RdAddr));

		-- Two stage synchronizer
		vi.RdAddrGraySync	:= ro.RdAddrGray;
		vi.RdAddrGray		:= ri.RdAddrGraySync;
		vo.WrAddrGraySync	:= ri.WrAddrGray;
		vo.WrAddrGray		:= ro.WrAddrGraySync;

		-- Gray->Bin involves some logic, needs additional FF
		vi.RdAddr		:= unsigned(GrayToBinary(ri.RdAddrGray));
		vo.WrAddr		:= unsigned(GrayToBinary(ro.WrAddrGray));

		-- *** Assign signal ***
		ri_next <= vi;
		ro_next <= vo;

	end process;

	--------------------------------------------------------------------------
	-- Sequential
	--------------------------------------------------------------------------
	p_seq_in : process(InClk)
	begin
		if rising_edge(InClk) then
			ri <= ri_next;
			if RstInInt = '1' then
				ri.WrAddr			<= (others => '0');
				ri.WrAddrGray		<= (others => '0');
				ri.RdAddrGraySync	<= (others => '0');
				ri.RdAddrGray		<= (others => '0');
			end if;
		end if;
	end process;

	p_seq_out : process(OutClk)
	begin
		if rising_edge(OutClk) then
			ro <= ro_next;
			if RstOutInt = '1' then
				ro.RdAddr			<= (others => '0');
				ro.RdAddrGray		<= (others => '0');
				ro.WrAddrGraySync	<= (others => '0');
				ro.WrAddrGray		<= (others => '0');
			end if;
		end if;
	end process;

	--------------------------------------------------------------------------
	-- Component Instantiations
	--------------------------------------------------------------------------
	i_ram : entity work.psi_common_tdp_ram_rbw
		generic map (
			Depth_g		=> Depth_g,
			Width_g		=> Width_g
		)
		port map (
			-- Port A
			ClkA		=> InClk,
			AddrA		=> std_logic_vector(ri.WrAddr(log2ceil(Depth_g)-1 downto 0)),
			WrA			=> RamWr,
			DinA		=> InData,
			DoutA		=> open,

			-- Port B
			ClkB		=> OutClk,
			AddrB		=> RamRdAddr,
			WrB			=> '0',
			DinB		=> (others => '0'),
			DoutB		=> OutData
		);

	-- only used for reset crossing and oring
	i_rst_cc : entity work.psi_common_pulse_cc
		port map (
			-- Clock Domain A
			ClkA		=> InClk,
			RstInA		=> InRst,
			RstOutA		=> RstInInt,
			PulseA		=> (others => '0'),

			-- Clock Domain B
			ClkB		=> OutClk,
			RstInB		=> OutRst,
			RstOutB		=> RstOutInt,
			PulseB		=> open
		);


end;





