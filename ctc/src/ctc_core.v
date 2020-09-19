//-----------------------------------------------------------------------------
// Block: ctc_core
// Description:
// This block implements 1 Counter/Timer Channel for Z80.
//
// CHANNEL CONTROL WORD (CCW)
// 0: 0=vector,  1=control
// 1: 0=enabled, 1=sw-reset
// 2: 0=no tc,   1=time constant follows
// 3: 0=start when tc loaded, 1 = start on clk_trig
// 4: 0=clktrig falling edge 1 = rising edge
// 5: 0=prescale 16 1=256
// 6: 0=timer mode  1=counter mode
// 7: 0:disable int 1=enable
// 8-bit time constant follows CCW with bit2=1
//
//------------------------------------------------------------------------------

module ctc_core #(
  parameter DWID = 8
)
(
  input                 clk,
  input                 reset_n,
  input                 ce_n,
  input                 cs,
  input                 m1_n,
  input                 rd_n,
  input                 iorq_n,
  input      [DWID-1:0] din,
  output     [DWID-1:0] dout,
  output                oe_n,
  input                 iei,
  output                ieo,
  output                int_n,

  input                 clk_trg,
  output                zc_to
);

  reg        [DWID-1:0] dout;
  reg                   oe_n;
  reg                   ieo;
  reg                   int_n;

  wire                  ccw_wstb;
  reg        [DWID-1:0] channel_control_word;
  wire                  select_vector_reg  = !din[0] && wstb;
  wire                  select_control_reg =  din[0] && wstb;
  wire                  ccw1_sw_reset      =  channel_control_word[1];
//   wire                ccw1_sw_reset      =  din[1] && ccw_wstb;
  wire                  time_constant_to_follow = din[2] && ccw_wstb;
  wire                  ccw3_auto_trig     = !channel_control_word[3];
  wire                  ccw3_ext_trig      =  channel_control_word[3];
  wire                  ccw4_trig_fe       = !channel_control_word[4]; // also sw trigger
  wire                  ccw4_trig_re       =  channel_control_word[4]; // also sw trigger
  wire                  ccw5_prescale16    = !channel_control_word[5]; // timer mode only
  wire                  ccw5_prescale256   =  channel_control_word[5]; // timer mode only
  wire                  ccw6_tim_mode      = !channel_control_word[6];
  wire                  ccw6_cnt_mode      =  channel_control_word[6];
  wire                  ccw7_int_en        =  channel_control_word[7];

  wire            [7:0] prescaler_factor = ccw5_prescale16 ? 8'h0F : 8'hFF;

  reg        [DWID-1:0] time_constant_word;
  reg        [DWID-1:0] down_counter;
  reg             [7:0] prescaler_counter;
  reg        [DWID-1:0] interrupt_vector_word;
  reg                   clk_trg2;
  reg                   clk_trg_re;
  reg                   clk_trg_fe;

  wire                  we1 = cs && rd_n && !iorq_n && !ce_n && m1_n;
  reg                   we2;
  wire                  wstb = we1 && !we2;
  reg                   time_constant_to_follow2;
  wire                  tc_wstb  = wstb && time_constant_to_follow2;
  assign                ccw_wstb = wstb && select_control_reg && !time_constant_to_follow2;
  wire                  vec_wstb = wstb && select_vector_reg && !time_constant_to_follow2;
  reg                   trig_on_time_constant_load;

  wire                  rd1 = cs && !rd_n && !iorq_n && !ce_n && m1_n;
  reg                   rd2;

  reg                   ccw4_trig_re2;
  wire                  sw_trig = ccw4_trig_re != ccw4_trig_re2 && !ccw1_sw_reset;

  wire                  trig_re_en = ccw3_ext_trig && ccw4_trig_re && !ccw1_sw_reset;
  wire                  trig_fe_en = ccw3_ext_trig && ccw4_trig_fe && !ccw1_sw_reset;
  reg                   trigger_pulse;
  reg                   triggered;
  reg                   zc_to;

  always @(posedge clk or negedge reset_n) begin
    if (!reset_n) begin
      we2                        <= 1'b0;
      rd2                        <= 1'b0;
      dout                       <= 'h0;
      channel_control_word       <= 'h0;
      time_constant_word         <= 'h0;
      time_constant_to_follow2   <= 1'b0;
      oe_n                       <= 1'b1;
      ieo                        <= 1'b0;
      int_n                      <= 1'b0;
      clk_trg2                   <= 1'b0;
      clk_trg_re                 <= 1'b0;
      clk_trg_fe                 <= 1'b0;
      trig_on_time_constant_load <= 1'b0;
      trigger_pulse              <= 1'b0;
      down_counter               <= 'h0;
      prescaler_counter          <= 8'h0;
      triggered                  <= 1'b0;
      ccw4_trig_re2              <= 1'b0;
      zc_to                      <= 1'b0;
    end
    else begin
      we2    <= we1; // used for edge detect
      rd2    <= rd1; // used for edge detect

      if (rd1 && !rd2) begin  // capture on rising edge of read
        dout <= down_counter;
        oe_n <= 1'b0;
      end
      else begin
        dout <= 'h0;
        oe_n <= 1'b1;
      end

      if (ccw_wstb && time_constant_to_follow) begin
        time_constant_to_follow2 <= 1'b1;
      end
      else if (tc_wstb) begin
        time_constant_to_follow2 <= 1'b0;
      end

      if (tc_wstb) begin
        time_constant_word <= din - 1;
      end

      if (ccw_wstb) begin
        channel_control_word <= din;
      end

      if (vec_wstb) begin
        interrupt_vector_word <= din;
      end

      trig_on_time_constant_load <= tc_wstb && ccw3_auto_trig && ccw6_tim_mode;
      ccw4_trig_re2 <=  ccw4_trig_re;
      clk_trg2      <=  clk_trg;
      clk_trg_re    <=  clk_trg && !clk_trg2 && trig_re_en;
      clk_trg_fe    <= !clk_trg &&  clk_trg2 && trig_fe_en;;
      trigger_pulse <= clk_trg_re || clk_trg_fe || trig_on_time_constant_load || sw_trig;

      if (ccw1_sw_reset) begin
        triggered <= 1'b0;
      end
      else if (trigger_pulse) begin
        triggered <= 1'b1;
      end

      if (ccw6_tim_mode && triggered) begin
        prescaler_counter <= (prescaler_counter==8'h0) ? prescaler_factor : prescaler_counter - 1;
        if (prescaler_counter==8'h0) begin
          down_counter <= (down_counter=='h0) ? time_constant_word : down_counter - 1;
        end
      end
      else begin
        prescaler_counter <= 'h0;
        down_counter <= 'h0;
      end

      zc_to <= triggered && down_counter=='h0;

    end
  end
endmodule





